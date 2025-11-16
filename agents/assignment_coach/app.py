import logging
import uuid
import json
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from datetime import datetime

from shared.models import TaskEnvelope, CompletionReport
from agents.assignment_coach import ltm, client

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ltm.init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health():
    return {"status": "healthy", "version": "1.0.0", "service": "assignment_coach_agent", "timestamp": datetime.utcnow().isoformat()}

@app.post('/process', response_model=CompletionReport)
async def process_task(req: Request):
    try:
        body = await req.json()
        task_envelope = TaskEnvelope(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Extract payload from task parameters
    # The supervisor sends RequestPayload which has: agentId, request, priority, modelOverride, autoRoute
    # The request field may contain JSON string with the assignment data
    request_text = task_envelope.task.parameters.get("request", "")
    payload = task_envelope.task.parameters.get("payload")
    intent = task_envelope.task.parameters.get("intent", "generate_assignment_guidance")
    
    # Try to parse request_text as JSON if payload is not provided
    if not payload and request_text:
        try:
            parsed_request = json.loads(request_text)
            # Check if it's the structured format with payload field
            if isinstance(parsed_request, dict) and "payload" in parsed_request:
                payload = parsed_request["payload"]
                intent = parsed_request.get("intent", intent)
            elif isinstance(parsed_request, dict):
                # If request_text is already the payload structure
                payload = parsed_request
        except json.JSONDecodeError:
            # If request_text is not JSON, try to extract assignment info from plain text
            # For now, we'll require structured input
            pass
    
    if not payload:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": "Missing 'payload' in task parameters. Please provide assignment data in the request field as JSON."}
        )
    
    # Validate intent (optional check)
    if intent and intent != "generate_assignment_guidance":
        _logger.warning(f"Unexpected intent '{intent}', proceeding anyway.")
    
    # Generate guidance using LangGraph workflow
    # The workflow handles: LTM check → Tools → Response generation → LTM save
    model_override = task_envelope.task.parameters.get("modelOverride")
    result = await client.generate_assignment_guidance(payload, model_override)

    if "error" in result:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": result["error"]}
        )
    
    try:
        # Try to parse the JSON response for better structure
        response_data = json.loads(result["output"])
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="SUCCESS",
            results={"output": result["output"], "response": response_data, "cached": False}
        )
    except json.JSONDecodeError:
        # If output is not JSON, return as string
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssignmentCoachAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="SUCCESS",
            results={"output": result["output"], "cached": False}
        )

