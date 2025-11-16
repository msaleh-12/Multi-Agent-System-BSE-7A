import logging
import uuid
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from datetime import datetime

from shared.models import TaskEnvelope, CompletionReport
from agents.assignment_coach import ltm, coach_agent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ltm.init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health():
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}

@app.post('/process', response_model=CompletionReport)
async def process_task(req: Request):
    try:
        body = await req.json()
        task_envelope = TaskEnvelope(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Extract the assignment coach specific payload
    payload = task_envelope.task.parameters.get("request")
    if not payload:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": "Missing 'request' in task parameters"}
        )

    # Check LTM first for similar assignments
    cached_output = await ltm.lookup(payload)
    if cached_output:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="SUCCESS",
            results={"output": cached_output, "cached": True}
        )

    # Process with LangGraph agent
    result = await coach_agent.process_assignment_request(payload)

    if "error" in result:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": result["error"]}
        )

    # Save to LTM and return success
    await ltm.save(payload, result["output"])
    return CompletionReport(
        message_id=str(uuid.uuid4()),
        sender="AssignmentCoachAgent",
        recipient=task_envelope.sender,
        related_message_id=task_envelope.message_id,
        status="SUCCESS",
        results=result
    )
