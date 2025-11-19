import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from shared.models import TaskEnvelope, CompletionReport

from .models import ResearchInput, ResearchOutput
from .search import search_papers
from .summarize import generate_summary

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "ResearchFinderAgent"}

@app.post("/process", response_model=CompletionReport)
async def process_task(req: Request):
    try:
        body = await req.json()
        task_envelope = TaskEnvelope(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Extract the data input field
    params = task_envelope.task.parameters
    data = params.get("data")

    if not data:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="ResearchFinderAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": "Missing 'data' field in task parameters"}
        )

    # Parse into model
    try:
        research_input = ResearchInput(
            topic=data.get("topic"),
            keywords=data.get("keywords", []),
            year_range={
                "from_year": data["year_range"]["from"],
                "to_year": data["year_range"]["to"],
            },
            max_results=data.get("max_results", 5)
        )
    except Exception as e:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="ResearchFinderAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": f"Invalid data format: {e}"}
        )

    # Search Papers
    papers = await search_papers(research_input)

    # Generate summary
    summary = generate_summary(papers, research_input.topic)

    # Prepare structured output
    output = {
        "summary": summary,
        "papers": [p.dict() for p in papers]
    }

    return CompletionReport(
        message_id=str(uuid.uuid4()),
        sender="ResearchFinderAgent",
        recipient=task_envelope.sender,
        related_message_id=task_envelope.message_id,
        status="SUCCESS",
        results=output
    )
