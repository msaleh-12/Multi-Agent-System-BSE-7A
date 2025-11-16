# Assignment Coach Agent

A minimal, production-ready agent that provides assignment understanding, task breakdown, resource suggestions, and progress guidance to students.

## Features

- ✅ **LangGraph Integration**: Uses LangGraph for workflow orchestration (no LangChain)
- ✅ **Vector Database**: ChromaDB for long-term memory with semantic search
- ✅ **Strict I/O Format**: Follows exact JSON input/output specification
- ✅ **Independent Operation**: Completely independent from other agents
- ✅ **Supervisor Integration**: Seamlessly integrates with supervisor routing
- ✅ **Memory-First Design**: Checks LTM before processing new requests

## Architecture

```
Assignment Coach Agent
├── app.py              # FastAPI endpoint
├── coach_agent.py      # LangGraph workflow
└── ltm.py             # ChromaDB vector memory
```

### LangGraph Workflow

```
Input → Parse → Summary → Task Plan → Resources → Feedback → Output
```

## Input Format

```json
{
  "agent_name": "assignment_coach_agent",
  "intent": "generate_assignment_guidance",
  "payload": {
    "student_id": "stu_001",
    "assignment_title": "AI Chatbot Design Report",
    "assignment_description": "...",
    "subject": "Artificial Intelligence",
    "deadline": "2025-10-20",
    "difficulty": "Intermediate",
    "student_profile": {
      "learning_style": "visual",
      "progress": 0.25,
      "skills": ["writing", "communication"],
      "weaknesses": ["time management"]
    }
  }
}
```

## Output Format

```json
{
  "agent_name": "assignment_coach_agent",
  "status": "success",
  "response": {
    "assignment_summary": "...",
    "task_plan": [{ "step": 1, "task": "...", "estimated_time": "2 days" }],
    "recommended_resources": [
      { "type": "article", "title": "...", "url": "..." }
    ],
    "feedback": "You have completed 25% of your work...",
    "motivation": "You're progressing well!...",
    "timestamp": "2025-10-05T19:45:00Z"
  }
}
```

## Installation

1. Install dependencies:

```bash
pip install -r agents/assignment_coach/requirements.txt
```

2. The agent will run on port 5011:

```bash
# Linux/Mac
./run_assignment_coach.sh

# Windows
uvicorn agents.assignment_coach.app:app --host 0.0.0.0 --port 5011 --reload
```

## Testing

```bash
pytest agents/assignment_coach/tests/
```

## Integration with Supervisor

The agent is automatically registered in `config/registry.json`:

```json
{
  "id": "assignment-coach",
  "name": "Assignment Coach Agent",
  "url": "http://localhost:5011",
  "description": "Provide assignment understanding, task breakdown, resource suggestions, and progress guidance",
  "capabilities": [
    "assignment-guidance",
    "task-planning",
    "resource-recommendation",
    "student-coaching"
  ]
}
```

## Vector Database (LTM)

- **Engine**: ChromaDB (persistent)
- **Location**: `./ltm_assignment_coach/`
- **Strategy**: Semantic similarity search on assignment title + subject + description
- **Threshold**: 0.3 (adjustable in `ltm.py`)

When a similar assignment is found, the cached response is returned immediately.

## Usage via Supervisor

```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"password"}'

# 2. Submit assignment coaching request
curl -X POST http://localhost:8000/api/supervisor/request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "assignment-coach",
    "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{...}}",
    "priority": 1
  }'
```

## Direct Agent Access

```bash
# Health check
curl http://localhost:5011/health

# API Documentation
http://localhost:5011/docs
```
