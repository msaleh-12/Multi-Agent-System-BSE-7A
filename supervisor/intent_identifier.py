# supervisor/intent_identifier.py
import logging
import json
import os
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from pathlib import Path # Ensure this is imported at the top

_logger = logging.getLogger(__name__)


# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    _logger.error("GEMINI_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Configuration
CONFIDENCE_THRESHOLD = 0.70  # Minimum confidence to proceed without clarification
MIN_ACCEPTABLE_CONFIDENCE = 0.50  # Below this, always ask for clarification
BASE_DIR = Path(__file__).parent.parent
REGISTRY_FILE = BASE_DIR / "config" / "registry.json"

def load_agent_descriptions_from_registry() -> Dict:
    """
    Load agent descriptions directly from registry.json.
    This ensures single source of truth for agent information.
    """
    try:
        with open(REGISTRY_FILE, 'r') as f:
            agents = json.load(f)
            
        agent_descriptions = {}
        for agent in agents:
            agent_id = agent.get('id')
            agent_descriptions[agent_id] = {
                "name": agent.get('name'),
                "description": agent.get('description'),
                "capabilities": agent.get('capabilities', []),
                "url": agent.get('url'),
                "keywords": agent.get('keywords', [])
            }
        
        _logger.info(f"Loaded {len(agent_descriptions)} agent descriptions from registry")
        return agent_descriptions
    
    except FileNotFoundError:
        _logger.error(f"Registry file not found at {REGISTRY_FILE}")
        return {}
    except Exception as e:
        _logger.error(f"Error loading registry: {e}")
        return {}

class IntentIdentifier:
    def __init__(self):
        # Use the correct Gemini model
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.agent_descriptions = load_agent_descriptions_from_registry()
        
    def _build_agent_context(self) -> str:
        """Build a formatted string of all available agents and their capabilities."""
        if not self.agent_descriptions:
            _logger.warning("No agent descriptions loaded, reloading from registry")
            self.agent_descriptions = load_agent_descriptions_from_registry()
        
        context = "Available Learning System Agents:\n\n"
        for agent_id, info in self.agent_descriptions.items():
            context += f"Agent ID: {agent_id}\n"
            context += f"Name: {info['name']}\n"
            context += f"Description: {info['description']}\n"
            context += f"Capabilities: {', '.join(info.get('capabilities', []))}\n"
            if info.get('keywords'):
                context += f"Keywords: {', '.join(info['keywords'])}\n"
            context += "\n"
        return context
    
    def _build_prompt(self, user_query: str, conversation_history: List[Dict] = None) -> str:
        """Build the prompt for Gemini to identify intent."""
        agent_context = self._build_agent_context()
        
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            history_context = "\n### Conversation History (Recent messages):\n"
            # Only use last 5 messages for context
            for msg in conversation_history[-5:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_context += f"{role}: {content}\n"
            history_context += "\nUse this conversation history to better understand the current user query.\n"
        
        prompt = f"""You are an expert intent classifier for an educational multi-agent system. Your task is to analyze student queries and determine which specialized learning agent should handle the request.

{agent_context}

{history_context}

### Current User Query: 
"{user_query}"

### Your Task:
Analyze the query carefully and determine:
1. Which agent is MOST appropriate to handle this request
2. How confident you are in this decision (0.0 to 1.0)
3. Whether the query is clear enough or needs clarification
4. What parameters can be extracted from the query

### Response Format:
Respond with ONLY a JSON object in this EXACT format (no markdown, no backticks):

{{
    "agent_id": "exact_agent_id_from_list_above",
    "confidence": 0.95,
    "reasoning": "Clear explanation of why this agent was chosen",
    "is_ambiguous": false,
    "clarifying_questions": [],
    "extracted_params": {{
        "topic": "extracted topic if mentioned",
        "subject": "extracted subject if mentioned",
        "difficulty": "beginner/intermediate/advanced if mentioned",
        "num_questions": "number if mentioned",
        "style": "citation style if mentioned",
        "any_other_relevant_param": "value"
    }},
    "alternative_agents": []
}}

### Decision Rules:

1. **High Confidence (0.8-1.0)**: 
   - Query clearly matches ONE agent's primary function
   - All key information is present
   - No ambiguity in intent

2. **Medium Confidence (0.5-0.79)**:
   - Query matches agent but missing some details
   - Could potentially match multiple agents
   - Consider listing alternatives

3. **Low Confidence (< 0.5)**:
   - Query is vague or unclear
   - Set "is_ambiguous": true
   - Provide 2-3 specific clarifying questions

4. **Agent Selection Priority**:
   - Match query keywords with agent keywords
   - Match query intent with agent description
   - Match query action (create/analyze/check/find) with agent capabilities
   - If no specific agent matches well, use "gemini-wrapper" for general queries

5. **Clarifying Questions Guidelines**:
   - Ask SPECIFIC questions that help identify the right agent
   - Focus on: What task? What subject? What type of help needed?
   - Keep questions simple and direct

6. **Parameter Extraction**:
   - Extract ALL relevant details mentioned in query
   - Include: topics, subjects, difficulty levels, quantities, formats, deadlines
   - Use null for parameters not mentioned

### Examples:

Query: "Create a quiz on Python with 10 questions"
→ agent_id: "adaptive_quiz_master_agent", confidence: 0.95, extracted_params: {{"topic": "Python", "num_questions": 10}}

Query: "Help me with my assignment"
→ is_ambiguous: true, clarifying_questions: ["What subject is your assignment on?", "What specific help do you need (understanding, breakdown, resources)?"]

Query: "Check if my essay is plagiarized"
→ agent_id: "plagiarism_prevention_agent", confidence: 0.90

Query: "Find papers on machine learning"
→ agent_id: "research_scout_agent", confidence: 0.92, extracted_params: {{"topic": "machine learning"}}

Query: "What is photosynthesis?"
→ agent_id: "gemini-wrapper", confidence: 0.85 (general knowledge question, no specialized agent needed)

Now analyze the current user query and respond with the JSON object."""

        return prompt
    
    async def identify_intent(
        self, 
        user_query: str, 
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Identify the intent and appropriate agent for a user query.
        
        Args:
            user_query: The user's current query
            conversation_history: List of previous messages for context
            
        Returns:
            Dict with agent_id, confidence, reasoning, and other metadata
        """
        try:
            prompt = self._build_prompt(user_query, conversation_history)
            
            _logger.info(f"Identifying intent for query: {user_query}")
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON response
            intent_result = json.loads(response_text)
            
            # Validate agent_id exists
            agent_id = intent_result.get("agent_id")
            if agent_id not in self.agent_descriptions:
                _logger.warning(f"LLM returned unknown agent_id: {agent_id}, defaulting to gemini-wrapper")
                intent_result["agent_id"] = "gemini-wrapper"
                intent_result["confidence"] = 0.5
                intent_result["reasoning"] += " (Original agent not found in registry, using fallback)"
            
            # Apply confidence threshold logic
            confidence = intent_result.get("confidence", 0.5)
            
            if confidence < MIN_ACCEPTABLE_CONFIDENCE:
                # Force clarification for very low confidence
                intent_result["is_ambiguous"] = True
                if not intent_result.get("clarifying_questions"):
                    intent_result["clarifying_questions"] = [
                        "Could you provide more details about what you need help with?",
                        "What subject or topic are you working on?",
                        "What is your main goal right now?"
                    ]
                _logger.info(f"Confidence {confidence} below threshold {MIN_ACCEPTABLE_CONFIDENCE}, requesting clarification")
            
            _logger.info(f"Intent identified: {intent_result.get('agent_id')} (confidence: {confidence:.2f})")
            
            return intent_result
            
        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse LLM response as JSON: {e}")
            _logger.error(f"Raw response: {response_text}")
            return self._fallback_intent(user_query)
            
        except Exception as e:
            _logger.error(f"Error in intent identification: {e}")
            return self._fallback_intent(user_query)
    
    def _fallback_intent(self, user_query: str) -> Dict:
        """Fallback when LLM fails - use keyword matching."""
        _logger.warning("Using fallback keyword-based intent identification")
        
        query_lower = user_query.lower()
        best_match = None
        best_score = 0
        
        for agent_id, info in self.agent_descriptions.items():
            keywords = info.get('keywords', [])
            score = sum(1 for keyword in keywords if keyword.lower() in query_lower)
            if score > best_score:
                best_score = score
                best_match = agent_id
        
        if best_match and best_score > 0:
            confidence = min(0.7, best_score * 0.2)
            return {
                "agent_id": best_match,
                "confidence": confidence,
                "reasoning": "Fallback keyword matching used",
                "is_ambiguous": confidence < CONFIDENCE_THRESHOLD,
                "clarifying_questions": [
                    "Could you provide more details about your request?",
                    "What specific help do you need?"
                ] if confidence < CONFIDENCE_THRESHOLD else [],
                "extracted_params": {},
                "alternative_agents": []
            }
        
        # Ultimate fallback to gemini-wrapper
        return {
            "agent_id": "gemini-wrapper",
            "confidence": 0.3,
            "reasoning": "No specific agent matched, using general LLM",
            "is_ambiguous": True,
            "clarifying_questions": [
                "What would you like help with?",
                "Could you describe your task in more detail?"
            ],
            "extracted_params": {},
            "alternative_agents": []
        }

# Global instance
_intent_identifier = None

def get_intent_identifier() -> IntentIdentifier:
    """Get or create the global intent identifier instance."""
    global _intent_identifier
    if _intent_identifier is None:
        _intent_identifier = IntentIdentifier()
    return _intent_identifier