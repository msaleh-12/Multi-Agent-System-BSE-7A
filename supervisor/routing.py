# supervisor/main.py
import logging
import asyncio
import yaml
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from shared.models import RequestPayload, RequestResponse, User
from supervisor import registry, memory_manager, auth, routing
from supervisor.worker_client import forward_to_agent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

HEALTH_CHECK_INTERVAL = config['supervisor'].get('health_check_interval', 15)

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
    payload: RequestPayload, 
    user: User = Depends(auth.require_auth),
    conversation_history: Optional[List[dict]] = None
):
    """
    Submit a request to the supervisor for routing to appropriate agent.
    
    Returns either:
    - RequestResponse: If agent successfully processes the request
    - Clarification request: If user query is ambiguous
    """
    
    # Get routing decision with intent identification
    routing_result = await routing.decide_agent(
        payload, 
        registry.list_agents(),
        conversation_history
    )
    
    # Check if clarification is needed
    if routing_result.get("needs_clarification", False):
        _logger.info("Query is ambiguous, requesting clarification from user")
        return {
            "status": "clarification_needed",
            "message": "I need more information to help you better.",
            "clarifying_questions": routing_result.get("clarifying_questions", []),
            "intent_info": routing_result.get("intent_info", {}),
            "suggestion": "Please provide more details so I can route you to the right specialist agent."
        }
    
    agent_ids = routing_result.get("agent_ids", [])
    intent_info = routing_result.get("intent_info", {})
    
    if not agent_ids:
        raise HTTPException(
            status_code=404, 
            detail="No suitable agent found for the request. Please try rephrasing your query."
        )
    
    # Handle multiple potential agents
    if len(agent_ids) > 1:
        _logger.info(f"Multiple agents can handle this request: {agent_ids}")
        
        # Check if all agents are healthy
        healthy_agents = [
            agent_id for agent_id in agent_ids 
            if registry.get_agent(agent_id) and registry.get_agent(agent_id).status == "healthy"
        ]
        
        if not healthy_agents:
            raise HTTPException(
                status_code=503,
                detail="All suitable agents are currently offline. Please try again later."
            )
        
        # For now, use the first healthy agent (primary choice)
        # In future, you could ask user to choose or run in parallel
        agent_id = healthy_agents[0]
        
        _logger.info(f"Selected primary agent: {agent_id} from {len(healthy_agents)} healthy options")
    else:
        agent_id = agent_ids[0]
    
    # Check if agent is healthy
    agent = registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in registry")
    
    if agent.status != "healthy":
        # Try to find an alternative healthy agent
        _logger.warning(f"Primary agent {agent_id} is {agent.status}, looking for alternatives")
        
        alternative_agents = routing_result.get("intent_info", {}).get("alternative_agents", [])
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
            raise HTTPException(
                status_code=503,
                detail=f"Agent {agent_id} is currently {agent.status}. No healthy alternatives available."
            )
    
    # Build agent-specific payload
    agent_payload = routing.build_agent_payload(agent_id, payload.request, intent_info)
    
    # Update the payload with agent-specific format
    payload_dict = payload.dict()
    payload_dict["agent_specific_data"] = agent_payload
    
    try:
        # Forward to selected agent
        _logger.info(f"Forwarding request to {agent_id}")
        rr = await forward_to_agent(agent_id, payload)
        
        # Store in memory if successful
        if not rr.error:
            memory_manager.store(agent_id, payload, rr)
        
        # Add intent information to response
        response_dict = rr.dict() if hasattr(rr, 'dict') else rr
        response_dict["intent_info"] = {
            "identified_agent": agent_id,
            "confidence": intent_info.get("confidence", 0.0),
            "reasoning": intent_info.get("reasoning", "")
        }
        
        return response_dict
        
    except Exception as e:
        _logger.error(f"Error forwarding to agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request with {agent_id}: {str(e)}"
        )

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