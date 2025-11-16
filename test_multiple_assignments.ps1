# Multiple Test Cases for Assignment Coach Agent
# Tests different subjects, difficulty levels, and student profiles

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "   Assignment Coach - Multiple Test Cases" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

# Login once
Write-Host "[LOGIN] Authenticating..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body (@{email="test@example.com"; password="password"} | ConvertTo-Json) -ContentType "application/json"
    $token = $response.token
    Write-Host "[OK] Login successful`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Login failed!" -ForegroundColor Red
    exit 1
}

$PASSED = 0
$FAILED = 0

# ======================================================================
# Test 1: Beginner Python Programming
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 1/8] Beginner Python Programming" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input1 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_101"
            assignment_title = "Build a Simple Calculator in Python"
            assignment_description = "Create a command-line calculator with basic arithmetic operations"
            subject = "Python Programming"
            deadline = "2025-11-25"
            difficulty = "Beginner"
            student_profile = @{
                learning_style = "hands-on"
                progress = 0.0
                skills = @("problem-solving")
                weaknesses = @("coding")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input1 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 1 - Beginner Python" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 1`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 1 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 2: Intermediate Web Development
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 2/8] Intermediate Web Development" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input2 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_102"
            assignment_title = "Responsive Portfolio Website"
            assignment_description = "Design and develop a responsive portfolio website using HTML, CSS, and JavaScript"
            subject = "Web Development"
            deadline = "2025-12-10"
            difficulty = "Intermediate"
            student_profile = @{
                learning_style = "visual"
                progress = 0.4
                skills = @("HTML", "CSS")
                weaknesses = @("JavaScript")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input2 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 2 - Intermediate Web Dev" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 2`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 2 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 3: Advanced Database Design
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 3/8] Advanced Database Design" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input3 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_103"
            assignment_title = "E-commerce Database Schema"
            assignment_description = "Design a normalized database schema for an e-commerce platform"
            subject = "Database Systems"
            deadline = "2025-12-20"
            difficulty = "Advanced"
            student_profile = @{
                learning_style = "reading"
                progress = 0.2
                skills = @("SQL")
                weaknesses = @("normalization")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input3 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 3 - Advanced Database" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 3`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 3 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 4: Intermediate Data Science
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 4/8] Intermediate Data Science" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input4 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_104"
            assignment_title = "Customer Churn Prediction"
            assignment_description = "Analyze customer dataset to predict churn using ML models"
            subject = "Data Science"
            deadline = "2025-12-05"
            difficulty = "Intermediate"
            student_profile = @{
                learning_style = "hands-on"
                progress = 0.6
                skills = @("Python", "statistics")
                weaknesses = @("machine learning")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input4 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 4 - Intermediate Data Science" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 4`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 4 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 5: Beginner Mobile App Design
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 5/8] Beginner Mobile App Design" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input5 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_105"
            assignment_title = "Fitness Tracking App Design"
            assignment_description = "Create wireframes and mockups for a mobile fitness app"
            subject = "Mobile App Design"
            deadline = "2025-11-30"
            difficulty = "Beginner"
            student_profile = @{
                learning_style = "visual"
                progress = 0.1
                skills = @("creativity")
                weaknesses = @("design tools")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input5 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 5 - Beginner Mobile Design" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 5`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 5 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 6: Advanced Cybersecurity
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 6/8] Advanced Cybersecurity" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input6 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_106"
            assignment_title = "Network Security Audit"
            assignment_description = "Conduct security audit and penetration testing of test network"
            subject = "Cybersecurity"
            deadline = "2025-12-18"
            difficulty = "Advanced"
            student_profile = @{
                learning_style = "hands-on"
                progress = 0.3
                skills = @("networking")
                weaknesses = @("documentation")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input6 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 6 - Advanced Cybersecurity" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 6`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 6 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 7: Intermediate AI/ML
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 7/8] Intermediate AI/ML" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input7 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_107"
            assignment_title = "Image Classification CNN"
            assignment_description = "Build CNN model to classify CIFAR-10 images"
            subject = "Artificial Intelligence"
            deadline = "2025-12-12"
            difficulty = "Intermediate"
            student_profile = @{
                learning_style = "mixed"
                progress = 0.35
                skills = @("Python")
                weaknesses = @("deep learning")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input7 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 7 - Intermediate AI/ML" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 7`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 7 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Test 8: Beginner Software Testing
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[Test 8/8] Beginner Software Testing" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$input8 = @{
    agentId = "assignment-coach"
    request = (@{
        agent_name = "assignment_coach_agent"
        intent = "generate_assignment_guidance"
        payload = @{
            student_id = "stu_108"
            assignment_title = "Library Management Test Plan"
            assignment_description = "Create comprehensive test plan for library management system"
            subject = "Software Testing"
            deadline = "2025-11-28"
            difficulty = "Beginner"
            student_profile = @{
                learning_style = "reading"
                progress = 0.5
                skills = @("documentation")
                weaknesses = @("automation")
            }
        }
    } | ConvertTo-Json -Depth 10)
    priority = 1
    autoRoute = $false
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/supervisor/request" -Method Post -Headers @{Authorization="Bearer $token"} -Body $input8 -ContentType "application/json" -TimeoutSec 30
    if ($result.agentId -eq "assignment-coach") {
        Write-Host "[PASSED] Test 8 - Beginner Testing" -ForegroundColor Green
        $guidance = $result.response | ConvertFrom-Json
        Write-Host "`nSUMMARY:" -ForegroundColor White
        Write-Host $guidance.response.assignment_summary -ForegroundColor Gray
        Write-Host "`nTASK PLAN:" -ForegroundColor White
        $guidance.response.task_plan | ForEach-Object { Write-Host "  [$($_.step_number)] $($_.task_name) - $($_.estimated_time)" -ForegroundColor Cyan; Write-Host "      $($_.description)" -ForegroundColor Gray }
        Write-Host "`nRESOURCES:" -ForegroundColor White
        $guidance.response.recommended_resources | ForEach-Object { Write-Host "  - $($_.type): $($_.title)" -ForegroundColor Yellow }
        Write-Host "`nFEEDBACK:" -ForegroundColor White
        Write-Host $guidance.response.personalized_feedback.progress_feedback -ForegroundColor Gray
        Write-Host $guidance.response.personalized_feedback.motivation -ForegroundColor Magenta
        Write-Host "`nExecution Time: $([math]::Round($result.metadata.executionTime, 2))ms`n" -ForegroundColor DarkGray
        $PASSED++
    } else {
        Write-Host "[FAILED] Test 8`n" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "[FAILED] Test 8 - $_`n" -ForegroundColor Red
    $FAILED++
}

# ======================================================================
# Final Summary
# ======================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   TEST SUMMARY" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Total Tests: 8" -ForegroundColor White
Write-Host "Passed: $PASSED" -ForegroundColor Green
Write-Host "Failed: $FAILED" -ForegroundColor Red
Write-Host "======================================================================`n" -ForegroundColor Cyan

if ($FAILED -eq 0) {
    Write-Host "[SUCCESS] All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[WARNING] Some tests failed" -ForegroundColor Yellow
    exit 1
}
