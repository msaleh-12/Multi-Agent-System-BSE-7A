from collections import deque
from typing import Dict, List
import yaml

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

STM_SIZE = config['supervisor']['stm_size']

_stm: Dict[str, deque] = {}

def store(agent_id: str, request, response):
    if agent_id not in _stm:
        _stm[agent_id] = deque(maxlen=STM_SIZE)
    
    interaction = {
        "message_id": response.message_id if hasattr(response, 'message_id') else None,
        "input": request.dict(),
        "output": response.dict(),
        "ts": response.timestamp.isoformat()
    }
    _stm[agent_id].append(interaction)

def get_history(agent_id: str) -> List[dict]:
    return list(_stm.get(agent_id, []))
