import json
import logging
from typing import List
import httpx
import yaml

from shared.models import Agent

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

REGISTRY_FILE = config['supervisor']['registry_file']
_agents = []
_logger = logging.getLogger(__name__)

def load_registry():
    global _agents
    try:
        with open(REGISTRY_FILE, 'r') as f:
            agents_data = json.load(f)
            _agents = [Agent(**data) for data in agents_data]
            _logger.info(f"Loaded {len(_agents)} agents from {REGISTRY_FILE}")
    except FileNotFoundError:
        _logger.error(f"Registry file not found at {REGISTRY_FILE}")
        _agents = []

async def health_check_agents():
    global _agents
    async with httpx.AsyncClient() as client:
        for agent in _agents:
            try:
                response = await client.get(f"{agent.url}/health", timeout=2.0)
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    agent.status = "healthy"
                else:
                    agent.status = "offline"
            except httpx.RequestError:
                agent.status = "offline"
    _logger.info("Agent health checks complete.")

def list_agents() -> List[Agent]:
    return _agents

def get_agent(agent_id: str) -> Agent | None:
    for agent in _agents:
        if agent.id == agent_id:
            return agent
    return None
