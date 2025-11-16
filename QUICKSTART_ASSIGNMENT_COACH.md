# Quick Start Guide - Assignment Coach Agent

## 🚀 Start the Services

### 1. Start all three services in separate terminals:

**Terminal 1 - Supervisor:**

```powershell
uvicorn supervisor.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Gemini Wrapper:**

```powershell
uvicorn agents.gemini_wrapper.app:app --host 0.0.0.0 --port 5010 --reload
```

**Terminal 3 - Assignment Coach:**

```powershell
uvicorn agents.assignment_coach.app:app --host 0.0.0.0 --port 5011 --reload
```

Or use the PowerShell scripts:

```powershell
.\run_supervisor.ps1          # Terminal 1
.\run_gemini.ps1              # Terminal 2
.\run_assignment_coach.ps1    # Terminal 3
```

## 🧪 Test the Agent

### Option 1: Run the test script

```powershell
python agents/assignment_coach/example_test.py
```

### Option 2: Manual API testing

**1. Login to get token:**

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body (@{email="test@example.com"; password="password"} | ConvertTo-Json) -ContentType "application/json"
$token = $response.token
```

**2. Check agent is registered:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/registry" -Headers @{Authorization="Bearer $token"}
```

**3. Submit assignment request:**

```powershell
$input = @{
    agent_name = "assignment_coach_agent"
    intent = "generate_assignment_guidance"
    payload = @{
        student_id = "stu_001"
        assignment_title = "AI Chatbot Design Report"
        assignment_description = "Prepare a detailed report explaining the architecture and training process of a conversational AI chatbot."
        subject = "Artificial Intelligence"
        deadline = "2025-10-20"
        difficulty = "Intermediate"
        student_profile = @{
            learning_style = "visual"
            progress = 0.25
            skills = @("writing", "communication")
            weaknesses = @("time management")
        }
    }
} | ConvertTo-Json -Depth 10

$payload = @{
    agentId = "assignment-coach"
    request = $input
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $payload -ContentType "application/json"
```

## 📊 Check Agent Status

**Direct health check:**

```powershell
curl http://localhost:5011/health
```

**Through supervisor:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/agent/assignment-coach/health" -Headers @{Authorization="Bearer $token"}
```

## 🎯 Features Verified

- ✅ LangGraph workflow (parse → summary → tasks → resources → feedback)
- ✅ ChromaDB vector database for long-term memory
- ✅ Semantic similarity search for cached responses
- ✅ Integration with supervisor agent
- ✅ Proper JSON input/output format
- ✅ Independent agent (doesn't depend on other agents)

## 📝 Example Response Format

```json
{
  "agent_name": "assignment_coach_agent",
  "status": "success",
  "response": {
    "assignment_summary": "...",
    "task_plan": [{ "step": 1, "task": "...", "estimated_time": "2 days" }],
    "recommended_resources": [
      { "type": "video", "title": "...", "url": "..." }
    ],
    "feedback": "...",
    "motivation": "...",
    "timestamp": "2025-11-16T..."
  }
}
```
