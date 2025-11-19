# supervisor/memory_manager.py
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from shared.models import RequestPayload, RequestResponse

_logger = logging.getLogger(__name__)

# In-memory storage for conversation history
# Format: {user_id: [{role, content, timestamp, agent_id, intent_info}, ...]}
_conversation_history = {}

# Maximum messages to keep per user
MAX_HISTORY_PER_USER = 50

def store(agent_id: str, payload: RequestPayload, response: RequestResponse):
    """
    Store a request-response pair in memory for future reference.
    This is used for analytics and debugging.
    """
    try:
        # You can implement persistent storage here (database, file, etc.)
        _logger.info(f"Stored interaction with {agent_id}")
    except Exception as e:
        _logger.error(f"Error storing interaction: {e}")

def store_conversation_message(
    user_id: str, 
    role: str, 
    content: str, 
    agent_id: Optional[str] = None,
    intent_info: Optional[Dict] = None
):
    """
    Store a conversation message for maintaining context.
    
    Args:
        user_id: Unique user identifier
        role: 'user' or 'assistant'
        content: The message content
        agent_id: Which agent handled this (if applicable)
        intent_info: Intent identification result (if applicable)
    """
    global _conversation_history
    
    if user_id not in _conversation_history:
        _conversation_history[user_id] = []
    
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "intent_info": intent_info
    }
    
    _conversation_history[user_id].append(message)
    
    # Keep only recent messages to prevent memory overflow
    if len(_conversation_history[user_id]) > MAX_HISTORY_PER_USER:
        _conversation_history[user_id] = _conversation_history[user_id][-MAX_HISTORY_PER_USER:]
    
    _logger.info(f"Stored conversation message for user {user_id} (total: {len(_conversation_history[user_id])})")

def get_conversation_history(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Retrieve recent conversation history for a user.
    
    Args:
        user_id: Unique user identifier
        limit: Maximum number of recent messages to return
        
    Returns:
        List of conversation messages (most recent last)
    """
    if user_id not in _conversation_history:
        return []
    
    history = _conversation_history[user_id]
    
    # Return most recent messages
    return history[-limit:] if len(history) > limit else history

def clear_conversation_history(user_id: str):
    """Clear conversation history for a specific user."""
    global _conversation_history
    if user_id in _conversation_history:
        del _conversation_history[user_id]
        _logger.info(f"Cleared conversation history for user {user_id}")

def get_conversation_summary(user_id: str) -> Dict:
    """
    Get a summary of the user's conversation history.
    
    Returns:
        Dict with statistics about the conversation
    """
    if user_id not in _conversation_history:
        return {
            "total_messages": 0,
            "agents_used": [],
            "last_interaction": None
        }
    
    history = _conversation_history[user_id]
    agents_used = set()
    
    for msg in history:
        if msg.get("agent_id"):
            agents_used.add(msg["agent_id"])
    
    return {
        "total_messages": len(history),
        "agents_used": list(agents_used),
        "last_interaction": history[-1]["timestamp"] if history else None,
        "user_message_count": sum(1 for msg in history if msg["role"] == "user"),
        "assistant_message_count": sum(1 for msg in history if msg["role"] == "assistant")
    }

def is_clarification_conversation(user_id: str, lookback: int = 3) -> bool:
    """
    Check if the recent conversation has been clarification-focused.
    This helps determine if we should continue asking questions or accept ambiguity.
    
    Args:
        user_id: Unique user identifier
        lookback: How many recent messages to check
        
    Returns:
        True if recent messages indicate ongoing clarification
    """
    history = get_conversation_history(user_id, limit=lookback)
    
    clarification_count = 0
    for msg in history:
        intent_info = msg.get("intent_info", {})
        if intent_info and intent_info.get("is_ambiguous", False):
            clarification_count += 1
    
    # If more than half of recent messages needed clarification, we're in clarification mode
    return clarification_count > (len(history) / 2) if history else False

def export_conversation_history(user_id: str, filepath: Optional[str] = None) -> str:
    """
    Export conversation history to JSON file.
    
    Args:
        user_id: User identifier
        filepath: Optional custom file path
        
    Returns:
        Path to exported file
    """
    if filepath is None:
        filepath = f"logs/conversation_history_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    history = _conversation_history.get(user_id, [])
    
    try:
        with open(filepath, 'w') as f:
            json.dump({
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(),
                "message_count": len(history),
                "messages": history
            }, f, indent=2)
        
        _logger.info(f"Exported conversation history to {filepath}")
        return filepath
    except Exception as e:
        _logger.error(f"Error exporting conversation history: {e}")
        return None