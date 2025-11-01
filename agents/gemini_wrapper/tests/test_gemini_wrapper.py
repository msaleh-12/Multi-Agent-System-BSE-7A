import pytest
from fastapi.testclient import TestClient
import uuid

from agents.gemini_wrapper.app import app
from shared.models import Task, TaskEnvelope

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_process_mock_request():
    task = Task(name="test_task", parameters={"request": "What is FastAPI?"})
    envelope = TaskEnvelope(
        message_id=str(uuid.uuid4()),
        sender="test_supervisor",
        recipient="gemini-wrapper",
        task=task
    )
    
    response = client.post("/process", json=envelope.dict())
    
    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "SUCCESS"
    assert "mock response" in report["results"]["output"]
    assert report["results"]["cached"] == False # First time, not cached

@pytest.mark.asyncio
async def test_ltm_caching():
    # This test should interact with the LTM directly or through the endpoint
    # to verify caching behavior.
    from agents.gemini_wrapper import ltm
    
    test_input = "This is a test for LTM."
    test_output = "This is a cached output."
    
    # Ensure it's not there first
    assert await ltm.lookup(test_input) is None
    
    # Save it
    await ltm.save(test_input, test_output)
    
    # Now it should be there
    assert await ltm.lookup(test_input) == test_output
