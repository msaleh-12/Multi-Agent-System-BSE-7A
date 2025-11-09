# supervisor/main.py
import logging
import asyncio
import yaml
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

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
    # In a real app, you'd have a proper user model and password hashing
    if "email" not in payload or "password" not in payload:
        raise HTTPException(status_code=400, detail="Email and password required")
    return auth.login(payload)

@app.post('/api/auth/logout')
async def logout(user: User = Depends(auth.require_auth)):
    # In a real stateless JWT setup, logout is often handled client-side.
    # This endpoint is for completeness.
    return {"message": "Logged out successfully"}

@app.get('/api/auth/me', response_model=User)
async def get_current_user(user: User = Depends(auth.require_auth)):
    return user

@app.get('/api/supervisor/registry')
async def get_registry(user: User = Depends(auth.require_auth)):
    return {"agents": registry.list_agents()}

@app.post('/api/supervisor/request', response_model=RequestResponse)
async def submit_request(payload: RequestPayload, user: User = Depends(auth.require_auth)):
    agent_ids = routing.decide_agent(payload, registry.list_agents())
    if not agent_ids:
        raise HTTPException(status_code=404, detail="No suitable agent found for the request.")
    
    # For this milestone, we only handle the first agent.
    agent_id = agent_ids[0]
    
    rr = await forward_to_agent(agent_id, payload)
    
    if not rr.error:
        memory_manager.store(agent_id, payload, rr)
        
    return rr

@app.get('/api/agent/{agent_id}/health')
async def get_agent_health(agent_id: str, user: User = Depends(auth.require_auth)):
    agent = registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": agent.status}
