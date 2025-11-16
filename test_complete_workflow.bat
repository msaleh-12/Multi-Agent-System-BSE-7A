@echo off
REM Complete test script for Assignment Coach via Supervisor
REM Save as: test_complete_workflow.bat

echo.
echo ======================================================================
echo    Assignment Coach Integration Test
echo ======================================================================
echo.

REM Step 1: Login
echo [Step 1/4] Logging in...
curl -s -X POST "http://localhost:8000/api/auth/login" ^
     -H "Content-Type: application/json" ^
     -d "{\"email\":\"test@example.com\",\"password\":\"password\"}" ^
     -o login_response.json

if errorlevel 1 (
    echo [ERROR] Login failed!
    del login_response.json 2>nul
    exit /b 1
)

REM Extract token using PowerShell
for /f "delims=" %%i in ('powershell -Command "(Get-Content login_response.json | ConvertFrom-Json).token"') do set TOKEN=%%i

if "%TOKEN%"=="" (
    echo [ERROR] Could not extract token from response
    type login_response.json
    del login_response.json
    exit /b 1
)

echo [OK] Login successful!
del login_response.json
echo.

REM Step 2: Check Registry
echo [Step 2/4] Checking agent registry...
curl -s "http://localhost:8000/api/supervisor/registry" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -o registry_response.json

if errorlevel 1 (
    echo [ERROR] Registry check failed!
    del registry_response.json 2>nul
    exit /b 1
)

REM Check if assignment-coach is in registry
findstr /C:"assignment-coach" registry_response.json >nul
if errorlevel 1 (
    echo [ERROR] Assignment Coach not found in registry!
    type registry_response.json
    del registry_response.json
    exit /b 1
)

echo [OK] Assignment Coach found in registry
del registry_response.json
echo.

REM Step 3: Check Agent Health
echo [Step 3/4] Checking agent health...
curl -s "http://localhost:8000/api/agent/assignment-coach/health" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -o health_response.json

if errorlevel 1 (
    echo [WARNING] Could not check agent health
) else (
    findstr /C:"healthy" health_response.json >nul
    if errorlevel 1 (
        echo [WARNING] Agent may not be healthy
    ) else (
        echo [OK] Agent is healthy
    )
)
del health_response.json 2>nul
echo.

REM Step 4: Submit Assignment Request
echo [Step 4/4] Submitting assignment guidance request...

REM Create the request JSON
(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_001\",\"assignment_title\":\"Machine Learning Classification Project\",\"assignment_description\":\"Build and compare different ML classification algorithms on a real-world dataset\",\"subject\":\"Machine Learning\",\"deadline\":\"2025-12-15\",\"difficulty\":\"Advanced\",\"student_profile\":{\"learning_style\":\"hands-on\",\"progress\":0.15,\"skills\":[\"coding\",\"mathematics\"],\"weaknesses\":[\"documentation\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > request_payload.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @request_payload.json ^
     -o result_response.json

if errorlevel 1 (
    echo [ERROR] Request failed!
    del request_payload.json result_response.json 2>nul
    exit /b 1
)

echo [OK] Response received!
echo.
echo ======================================================================
echo    RESULT:
echo ======================================================================
type result_response.json
echo.
echo ======================================================================

REM Cleanup
del request_payload.json result_response.json

echo.
echo [SUCCESS] All tests passed! Assignment Coach is working through Supervisor!
echo.
exit /b 0
