# supervisor/main.py
import logging
import asyncio
import yaml
from fastapi import FastAPI, Depends, HTTPException, Body
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel

from shared.models import RequestPayload, RequestResponse, User
from supervisor import registry, memory_manager, auth, routing
from supervisor.worker_client import forward_to_agent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

HEALTH_CHECK_INTERVAL = config['supervisor'].get('health_check_interval', 15)
MAX_CLARIFICATION_ATTEMPTS = 3  # Maximum times to ask for clarification before giving up

# Request model that includes conversation context
class EnhancedRequestPayload(BaseModel):
    request: str
    agentId: Optional[str] = None
    autoRoute: bool = True
    conversationId: Optional[str] = None  # For tracking conversation threads
    includeHistory: bool = True  # Whether to use conversation history for context

async def periodic_health_checks():
    """Periodically run health checks for all registered agents."""
    while True:
        _logger.info("Running periodic agent health checks...")
        await registry.health_check_agents()
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    _logger.info("Supervisor starting up...")
    registry.load_registry()
    # Initial health check
    await registry.health_check_agents()
    
    # Start periodic health checks as a background task
    health_check_task = asyncio.create_task(periodic_health_checks())
    
    yield
    
    # On shutdown
    _logger.info("Supervisor shutting down.")
    health_check_task.cancel()
    try:
        await health_check_task
    except asyncio.CancelledError:
        _logger.info("Health check task cancelled successfully.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/api/auth/login')
async def login(payload: dict):
    if "email" not in payload or "password" not in payload:
        raise HTTPException(status_code=400, detail="Email and password required")
    return auth.login(payload)

@app.post('/api/auth/logout')
async def logout(user: User = Depends(auth.require_auth)):
    return {"message": "Logged out successfully"}

@app.get('/api/auth/me', response_model=User)
async def get_current_user(user: User = Depends(auth.require_auth)):
    return user

@app.get('/api/supervisor/registry')
async def get_registry(user: User = Depends(auth.require_auth)):
    return {"agents": registry.list_agents()}

@app.post('/api/supervisor/request')
async def submit_request(
    payload: EnhancedRequestPayload, 
    user: User = Depends(auth.require_auth)
):
    """
    Submit a request to the supervisor for routing to appropriate agent.
    Maintains conversation context and handles iterative clarification.
    
    Returns either:
    - RequestResponse: If agent successfully processes the request
    - Clarification request: If user query is ambiguous
    """
    
    user_id = user.id
    user_query = payload.request
    
    # Get conversation history if enabled
    conversation_history = None
    if payload.includeHistory:
        conversation_history = memory_manager.get_conversation_history(user_id, limit=10)
        _logger.info(f"Retrieved {len(conversation_history)} previous messages for context")
    
    # Store user message
    memory_manager.store_conversation_message(
        user_id=user_id,
        role="user",
        content=user_query
    )
    
    # Check if we've been asking for clarification too many times
    recent_clarifications = sum(
        1 for msg in (conversation_history or [])[-MAX_CLARIFICATION_ATTEMPTS:]
        if msg.get("intent_info", {}).get("is_ambiguous", False)
    )
    
    if recent_clarifications >= MAX_CLARIFICATION_ATTEMPTS:
        _logger.warning(f"User {user_id} has received {recent_clarifications} clarification requests. Proceeding with best guess.")
        # Force routing to gemini-wrapper for general handling
        agent_id = "gemini-wrapper"
        routing_result = {
            "agent_ids": [agent_id],
            "intent_info": {
                "agent_id": agent_id,
                "confidence": 0.5,
                "reasoning": "Query remains unclear after multiple clarification attempts. Using general assistant.",
                "is_ambiguous": False
            },
            "needs_clarification": False
        }
    else:
        # Get routing decision with intent identification
        routing_result = await routing.decide_agent(
            payload, 
            registry.list_agents(),
            conversation_history
        )
    
    intent_info = routing_result.get("intent_info", {})
    
    # Check if clarification is needed
    if routing_result.get("needs_clarification", False):
        _logger.info("Query is ambiguous, requesting clarification from user")
        
        clarification_response = {
            "status": "clarification_needed",
            "message": "I need a bit more information to help you better.",
            "clarifying_questions": routing_result.get("clarifying_questions", []),
            "intent_info": intent_info,
            "suggestions": [
                "Please be more specific about what you need",
                "Try mentioning the subject or topic you're working on",
                "Let me know what type of help you're looking for"
            ],
            "clarification_count": recent_clarifications + 1,
            "max_clarifications": MAX_CLARIFICATION_ATTEMPTS
        }
        
        # Store assistant clarification request
        memory_manager.store_conversation_message(
            user_id=user_id,
            role="assistant",
            content=f"Clarification requested: {clarification_response['message']}",
            intent_info=intent_info
        )
        
        return clarification_response
    
    agent_ids = routing_result.get("agent_ids", [])
    
    if not agent_ids:
        error_message = "I couldn't identify the right specialist for your request. Could you try rephrasing or providing more details?"
        
        memory_manager.store_conversation_message(
            user_id=user_id,
            role="assistant",
            content=error_message,
            intent_info=intent_info
        )
        
        raise HTTPException(status_code=404, detail=error_message)
    
    # Handle multiple potential agents
    if len(agent_ids) > 1:
        _logger.info(f"Multiple agents can handle this request: {agent_ids}")
        
        # Check if all agents are healthy
        healthy_agents = [
            agent_id for agent_id in agent_ids 
            if registry.get_agent(agent_id) and registry.get_agent(agent_id).status == "healthy"
        ]
        
        if not healthy_agents:
            error_message = "All suitable agents are currently offline. Please try again later."
            memory_manager.store_conversation_message(
                user_id=user_id,
                role="assistant",
                content=error_message
            )
            raise HTTPException(status_code=503, detail=error_message)
        
        # Use the first healthy agent (primary choice)
        agent_id = healthy_agents[0]
        _logger.info(f"Selected primary agent: {agent_id} from {len(healthy_agents)} healthy options")
    else:
        agent_id = agent_ids[0]
    
    # Check if agent is healthy
    agent = registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in registry")
    
    if agent.status != "healthy":
        _logger.warning(f"Primary agent {agent_id} is {agent.status}, looking for alternatives")
        
        alternative_agents = intent_info.get("alternative_agents", [])
        healthy_alternative = None
        
        for alt_agent_id in alternative_agents:
            alt_agent = registry.get_agent(alt_agent_id)
            if alt_agent and alt_agent.status == "healthy":
                healthy_alternative = alt_agent_id
                break
        
        if healthy_alternative:
            _logger.info(f"Using alternative healthy agent: {healthy_alternative}")
            agent_id = healthy_alternative
        else:
            error_message = f"Agent {agent_id} is currently {agent.status}. No healthy alternatives available."
            memory_manager.store_conversation_message(
                user_id=user_id,
                role="assistant",
                content=error_message
            )
            raise HTTPException(status_code=503, detail=error_message)
    
    # Build agent-specific payload
    agent_payload = routing.build_agent_payload(agent_id, payload.request, intent_info)
    
    # Update the payload with agent-specific format
    payload_dict = payload.dict()
    payload_dict["agent_specific_data"] = agent_payload
    
    try:
        # Forward to selected agent
        _logger.info(f"Forwarding request to {agent_id} with confidence {intent_info.get('confidence', 0):.2f}")
        
        # Convert back to RequestPayload for forwarding
        forward_payload = RequestPayload(**payload_dict)
        rr = await forward_to_agent(agent_id, forward_payload)
        
        # Store in memory if successful
        if not rr.error:
            memory_manager.store(agent_id, forward_payload, rr)
        
        # Get the response content
        response_content = rr.response if hasattr(rr, 'response') else str(rr)
        
        # Store assistant response with intent info
        memory_manager.store_conversation_message(
            user_id=user_id,
            role="assistant",
            content=response_content,
            agent_id=agent_id,
            intent_info=intent_info
        )
        
        # Add metadata to response
        response_dict = rr.dict() if hasattr(rr, 'dict') else {"response": str(rr)}
        response_dict["metadata"] = {
            "identified_agent": agent_id,
            "agent_name": agent.name if agent else agent_id,
            "confidence": intent_info.get("confidence", 0.0),
            "reasoning": intent_info.get("reasoning", ""),
            "extracted_params": intent_info.get("extracted_params", {}),
            "conversation_length": len(conversation_history) if conversation_history else 0
        }
        
        return response_dict
        
    except Exception as e:
        _logger.error(f"Error forwarding to agent {agent_id}: {e}")
        error_message = f"Failed to process request with {agent_id}: {str(e)}"
        
        memory_manager.store_conversation_message(
            user_id=user_id,
            role="assistant",
            content=error_message
        )
        
        raise HTTPException(status_code=500, detail=error_message)

@app.get('/api/agent/{agent_id}/health')
async def get_agent_health(agent_id: str, user: User = Depends(auth.require_auth)):
    agent = registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": agent.status}

@app.post('/api/supervisor/identify-intent')
async def identify_intent_endpoint(
    payload: dict,
    user: User = Depends(auth.require_auth)
):
    """
    Standalone endpoint to identify intent without executing.
    Useful for testing and debugging.
    """
    from supervisor.intent_identifier import get_intent_identifier
    
    user_query = payload.get("query", "")
    conversation_history = payload.get("conversation_history", None)
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        intent_identifier = get_intent_identifier()
        result = await intent_identifier.identify_intent(user_query, conversation_history)
        return result
    except Exception as e:
        _logger.error(f"Error in intent identification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/supervisor/conversation/history')
async def get_conversation_history_endpoint(
    user: User = Depends(auth.require_auth),
    limit: int = 10
):
    """Get conversation history for the current user."""
    history = memory_manager.get_conversation_history(user.id, limit=limit)
    return {
        "user_id": user.id,
        "messages": history,
        "count": len(history)
    }

@app.get('/api/supervisor/conversation/summary')
async def get_conversation_summary_endpoint(user: User = Depends(auth.require_auth)):
    """Get a summary of the user's conversation."""
    summary = memory_manager.get_conversation_summary(user.id)
    return summary

@app.delete('/api/supervisor/conversation/clear')
async def clear_conversation_history_endpoint(user: User = Depends(auth.require_auth)):
    """Clear conversation history for the current user."""
    memory_manager.clear_conversation_history(user.id)
    return {"message": "Conversation history cleared successfully"}