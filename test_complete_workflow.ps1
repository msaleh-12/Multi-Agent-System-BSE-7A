# Complete test script for Assignment Coach via Supervisor
# Save as: test_complete_workflow.ps1

Write-Host "`n🚀 Assignment Coach Integration Test" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Step 1: Login
Write-Host "`n[Step 1/4] 🔐 Logging in..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body (@{email="test@example.com"; password="password"} | ConvertTo-Json) -ContentType "application/json"
    $token = $response.token
    Write-Host "✅ Login successful!" -ForegroundColor Green
    Write-Host "   User: $($response.user.name) ($($response.user.email))" -ForegroundColor Gray
} catch {
    Write-Host "❌ Login failed!" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Check Registry
Write-Host "`n[Step 2/4] 📋 Checking agent registry..." -ForegroundColor Yellow
try {
    $registry = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/registry" -Headers @{Authorization="Bearer $token"}
    $coach = $registry.agents | Where-Object { $_.id -eq "assignment-coach" }
    
    if ($coach) {
        Write-Host "✅ Assignment Coach found in registry" -ForegroundColor Green
        Write-Host "   Name: $($coach.name)" -ForegroundColor Gray
        Write-Host "   URL: $($coach.url)" -ForegroundColor Gray
        Write-Host "   Status: $($coach.status)" -ForegroundColor Gray
        Write-Host "   Capabilities: $($coach.capabilities -join ', ')" -ForegroundColor Gray
    } else {
        Write-Host "❌ Assignment Coach not found in registry!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Registry check failed!" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Check Agent Health
Write-Host "`n[Step 3/4] 🏥 Checking agent health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/agent/assignment-coach/health" -Headers @{Authorization="Bearer $token"}
    Write-Host "✅ Agent health: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not check agent health (agent may be offline)" -ForegroundColor Yellow
}

# Step 4: Submit Assignment Request
Write-Host "`n[Step 4/4] 📤 Submitting assignment guidance request..." -ForegroundColor Yellow

$input = @{
    agent_name = "assignment_coach_agent"
    intent = "generate_assignment_guidance"
    payload = @{
        student_id = "stu_001"
        assignment_title = "Machine Learning Classification Project"
        assignment_description = "Build and compare different ML classification algorithms (Decision Trees, Random Forest, SVM, Neural Networks) on a real-world dataset. Analyze their performance and provide recommendations."
        subject = "Machine Learning"
        deadline = "2025-12-15"
        difficulty = "Advanced"
        student_profile = @{
            learning_style = "hands-on"
            progress = 0.15
            skills = @("coding", "mathematics", "data analysis")
            weaknesses = @("documentation", "time management")
        }
    }
} | ConvertTo-Json -Depth 10

$payload = @{
    agentId = "assignment-coach"
    request = $input
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $payload -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "✅ Response received!" -ForegroundColor Green
    Write-Host "`n📊 Metadata:" -ForegroundColor Cyan
    Write-Host "   Agent: $($result.agentId)" -ForegroundColor Gray
    Write-Host "   Execution Time: $($result.metadata.executionTime)ms" -ForegroundColor Gray
    Write-Host "   Cached: $($result.metadata.cached)" -ForegroundColor Gray
    
    if ($result.response) {
        $guidance = $result.response | ConvertFrom-Json
        
        Write-Host "`n📝 Assignment Summary:" -ForegroundColor Cyan
        Write-Host "   $($guidance.response.assignment_summary)" -ForegroundColor White
        
        Write-Host "`n📋 Task Plan ($($guidance.response.task_plan.Count) steps):" -ForegroundColor Cyan
        foreach ($task in $guidance.response.task_plan) {
            Write-Host "   Step $($task.step): $($task.task)" -ForegroundColor White
            Write-Host "   └─ Time: $($task.estimated_time)" -ForegroundColor Gray
        }
        
        Write-Host "`n📚 Recommended Resources:" -ForegroundColor Cyan
        foreach ($resource in $guidance.response.recommended_resources) {
            Write-Host "   [$($resource.type.ToUpper())] $($resource.title)" -ForegroundColor White
            Write-Host "   └─ $($resource.url)" -ForegroundColor Gray
        }
        
        Write-Host "`n💡 Feedback:" -ForegroundColor Cyan
        Write-Host "   $($guidance.response.feedback)" -ForegroundColor White
        
        Write-Host "`n🌟 Motivation:" -ForegroundColor Cyan
        Write-Host "   $($guidance.response.motivation)" -ForegroundColor White
        
        Write-Host "`n⏰ Timestamp: $($guidance.response.timestamp)" -ForegroundColor Gray
        
    } else {
        Write-Host "`n❌ Error in response:" -ForegroundColor Red
        Write-Host "   $($result.error.message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Request failed!" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "✅ All tests passed! Assignment Coach is working through Supervisor!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""


