import logging
from typing import List
import yaml

from shared.models import RequestPayload, Agent

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

_logger = logging.getLogger(__name__)

def decide_agent(payload: RequestPayload, agents: List[Agent]) -> List[str]:
    if payload.agentId and not payload.autoRoute:
        return [payload.agentId]

    # Simple keyword-based routing for now.
    # In a real system, this would be a more sophisticated model.
    if "generate" in payload.request.lower() or "summarize" in payload.request.lower():
        for agent in agents:
            if "text-generation" in agent.capabilities:
                _logger.info(f"Routing to {agent.id} based on keywords.")
                return [agent.id]
            
    # Default to gemini-wrapper if no other agent is found
    _logger.warning("No specific agent found, defaulting to gemini-wrapper.")
    return ["gemini-wrapper"]
