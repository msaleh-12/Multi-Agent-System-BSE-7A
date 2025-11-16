# Multi-Agent Backend

This repository contains the backend for a multi-agent system, featuring a Supervisor and pluggable worker agents. This version includes:
- `gemini-wrapper` agent (for text generation)
- `assignment-coach` agent (for assignment guidance and task planning)

## Project Structure

```
/
├── config/
│   ├── registry.json         # Agent registration file
│   └── settings.yaml         # Main configuration for services
├── supervisor/               # Supervisor FastAPI application
│   ├── __init__.py
│   ├── main.py               # Main FastAPI app for supervisor
│   ├── auth.py               # Authentication logic
│   ├── memory_manager.py     # Short-term memory handler
│   ├── registry.py           # Agent registry management
│   ├── routing.py            # Request routing logic
│   ├── worker_client.py      # Client for communicating with workers
│   └── tests/                # Tests for the supervisor
├── agents/
│   ├── gemini_wrapper/       # Gemini-wrapper worker agent
│   │   ├── __init__.py
│   │   ├── app.py            # Main FastAPI app for the worker
│   │   ├── client.py         # Logic for calling Gemini API or mock
│   │   ├── ltm.py            # Long-term memory (SQLite)
│   │   └── tests/            # Tests for the gemini wrapper
│   └── assignment_coach/     # Assignment Coach worker agent
│       ├── __init__.py
│       ├── app.py            # Main FastAPI app for assignment coach
│       ├── client.py         # Assignment guidance generation logic
│       └── ltm.py            # Long-term memory (SQLite)
├── shared/
│   └── models.py             # Pydantic models shared across services
├── tests/
│   └── integration_test.py   # Manual integration test script
├── .env.example              # Example environment file for cloud mode
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── run_supervisor.sh         # Script to run the supervisor (Linux/Mac)
├── run_supervisor.bat        # Script to run the supervisor (Windows)
├── run_gemini.sh             # Script to run the gemini wrapper (Linux/Mac)
├── run_gemini.bat            # Script to run the gemini wrapper (Windows)
├── run_assignment_coach.sh   # Script to run assignment coach (Linux/Mac)
├── run_assignment_coach.bat  # Script to run assignment coach (Windows)
└── test_assignment_coach.py  # Test script for assignment coach agent
```

## Quickstart

### 1. Installation

Create a virtual environment and install the required packages.

**On Windows (PowerShell or Command Prompt):**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**On Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Running the Services

You need to run the Supervisor and at least one worker agent. For full functionality, run all services in separate terminals.

**On Windows:**

**Terminal 1: Run the Supervisor**
```powershell
# Make sure your virtual environment is activated first
venv\Scripts\activate
run_supervisor.bat
```

**Terminal 2: Run the Gemini Wrapper** (optional, for text generation)
```powershell
venv\Scripts\activate
run_gemini.bat
```

**Terminal 3: Run the Assignment Coach Agent** (optional, for assignment guidance)
```powershell
venv\Scripts\activate
run_assignment_coach.bat
```

**On Linux/Mac:**

**Terminal 1: Run the Supervisor**
```bash
chmod +x run_supervisor.sh
./run_supervisor.sh
```

**Terminal 2: Run the Gemini Wrapper** (optional)
```bash
chmod +x run_gemini.sh
./run_gemini.sh
```

**Terminal 3: Run the Assignment Coach Agent** (optional)
```bash
chmod +x run_assignment_coach.sh
./run_assignment_coach.sh
```

**Service URLs:**
- Supervisor: `http://127.0.0.1:8000`
- Gemini Wrapper: `http://127.0.0.1:5010` (runs in `mock` mode by default)
- Assignment Coach: `http://127.0.0.1:5020` (runs in `mock` mode by default)

## Agent Modes

Both `gemini-wrapper` and `assignment-coach` agents can run in two modes, configured in `config/settings.yaml`.

*   **`mock` mode (default):** No external API calls are made. The agent returns deterministic mock responses. This is useful for local development and testing without needing API keys.
*   **`cloud` mode:** The agent calls a real Gemini API. To enable this, you must:
    1.  Set `mode: "cloud"` or `mode: "auto"` in `config/settings.yaml` for the respective agent.
    2.  Create a `.env` file by copying `.env.example`.
    3.  Fill in your `GEMINI_API_KEY` in the `.env` file.

## Assignment Coach Agent

The Assignment Coach Agent provides:
- **Assignment Understanding**: Summarizes assignment requirements
- **Task Breakdown**: Creates step-by-step task plans with time estimates
- **Resource Recommendations**: Suggests learning resources based on student learning style
- **Progress Guidance**: Provides personalized feedback based on student profile
- **Motivation**: Delivers encouraging messages to keep students on track

### Technical Implementation

The Assignment Coach Agent follows all requirements:
- ✅ **Uses LangGraph**: Implements workflow using LangGraph (no LangChain)
- ✅ **Vector DB for LTM**: Uses ChromaDB for semantic similarity search in long-term memory
- ✅ **Tools Framework**: Includes tools for time estimation, resource suggestion, task breakdown, and deadline calculation
- ✅ **Semantic Search**: Checks LTM first using semantic similarity (not exact match)
- ✅ **JSON Output**: All responses are in standardized JSON format
- ✅ **Independent I/O**: Input and output formats are independent
- ✅ **Supervisor Integration**: Fully integrated with the supervisor system

### Using the Assignment Coach Agent

**Via Supervisor API:**

```bash
# 1. Login first
TOKEN=$(curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"password"}' | jq -r '.token')

# 2. Send assignment request
curl -X POST http://127.0.0.1:8000/api/supervisor/request \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "agentId": "assignment-coach",
    "request": "{\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_001\",\"assignment_title\":\"AI Chatbot Design Report\",\"assignment_description\":\"Prepare a detailed report explaining the architecture and training process of a conversational AI chatbot.\",\"subject\":\"Artificial Intelligence\",\"deadline\":\"2025-10-20\",\"difficulty\":\"Intermediate\",\"student_profile\":{\"learning_style\":\"visual\",\"progress\":0.25,\"skills\":[\"writing\",\"communication\"],\"weaknesses\":[\"time management\"]}}}",
    "priority": 1
  }'
```

**Test Script:**

Run the test script to verify the Assignment Coach Agent:
```bash
python test_assignment_coach.py
```

## Running Tests

### Unit Tests

To run the unit tests for both services, use `pytest`:

```bash
pytest
```

### Integration Test

A manual integration test script is provided in `tests/integration_test.py`. Make sure both services are running before executing it.

```bash
python tests/integration_test.py
```

## Example API Usage

Here are some `curl` commands to interact with the Supervisor API.

### 1. Login

First, log in to get an authentication token. The default test user is `test@example.com` with password `password`.

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"test@example.com", "password":"password"}'
```

This will return a JSON object with a `token`. Copy the token for the next step.

### 2. Submit a Request

Replace `<TOKEN>` with the token you received.

```bash
TOKEN="<YOUR_TOKEN_HERE>"

curl -X POST http://127.0.0.1:8000/api/supervisor/request \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"agentId":"gemini-wrapper","request":"Summarize: The impact of AI on modern software development.","priority":1}'
```

You should receive a `RequestResponse` from the `gemini-wrapper` agent. In `mock` mode, the response will be a templated message. In `cloud` mode, it will be the output from the configured LLM.
