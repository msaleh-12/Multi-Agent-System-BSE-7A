@echo off
REM Multiple Test Cases for Assignment Coach Agent
REM Tests different subjects, difficulty levels, and student profiles

echo.
echo ======================================================================
echo    Assignment Coach - Multiple Test Cases
echo ======================================================================
echo.

REM Login once
echo [LOGIN] Authenticating...
curl -s -X POST "http://localhost:8000/api/auth/login" ^
     -H "Content-Type: application/json" ^
     -d "{\"email\":\"test@example.com\",\"password\":\"password\"}" ^
     -o login_response.json

if errorlevel 1 (
    echo [ERROR] Login failed!
    del login_response.json 2>nul
    exit /b 1
)

for /f "delims=" %%i in ('powershell -Command "(Get-Content login_response.json | ConvertFrom-Json).token"') do set TOKEN=%%i
del login_response.json

if "%TOKEN%"=="" (
    echo [ERROR] Could not extract token
    exit /b 1
)

echo [OK] Login successful
echo.

set PASSED=0
set FAILED=0

REM ======================================================================
REM Test 1: Beginner Python Programming
REM ======================================================================
echo ======================================================================
echo [Test 1/8] Beginner Python Programming
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_101\",\"assignment_title\":\"Build a Simple Calculator in Python\",\"assignment_description\":\"Create a command-line calculator with basic arithmetic operations\",\"subject\":\"Python Programming\",\"deadline\":\"2025-11-25\",\"difficulty\":\"Beginner\",\"student_profile\":{\"learning_style\":\"hands-on\",\"progress\":0.0,\"skills\":[\"problem-solving\"],\"weaknesses\":[\"coding\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test1.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test1.json ^
     -o result1.json

findstr /C:"assignment-coach" result1.json >nul
if errorlevel 1 (
    echo [FAILED] Test 1
    type result1.json
    set /a FAILED+=1
) else (
    echo [PASSED] Test 1 - Beginner Python
    set /a PASSED+=1
)
del test1.json result1.json
echo.

REM ======================================================================
REM Test 2: Intermediate Web Development
REM ======================================================================
echo ======================================================================
echo [Test 2/8] Intermediate Web Development
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_102\",\"assignment_title\":\"Responsive Portfolio Website\",\"assignment_description\":\"Design and develop a responsive portfolio website using HTML, CSS, and JavaScript\",\"subject\":\"Web Development\",\"deadline\":\"2025-12-10\",\"difficulty\":\"Intermediate\",\"student_profile\":{\"learning_style\":\"visual\",\"progress\":0.4,\"skills\":[\"HTML\",\"CSS\"],\"weaknesses\":[\"JavaScript\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test2.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test2.json ^
     -o result2.json

findstr /C:"assignment-coach" result2.json >nul
if errorlevel 1 (
    echo [FAILED] Test 2
    set /a FAILED+=1
) else (
    echo [PASSED] Test 2 - Intermediate Web Dev
    set /a PASSED+=1
)
del test2.json result2.json
echo.

REM ======================================================================
REM Test 3: Advanced Database Design
REM ======================================================================
echo ======================================================================
echo [Test 3/8] Advanced Database Design
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_103\",\"assignment_title\":\"E-commerce Database Schema\",\"assignment_description\":\"Design a normalized database schema for an e-commerce platform\",\"subject\":\"Database Systems\",\"deadline\":\"2025-12-20\",\"difficulty\":\"Advanced\",\"student_profile\":{\"learning_style\":\"reading\",\"progress\":0.2,\"skills\":[\"SQL\"],\"weaknesses\":[\"normalization\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test3.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test3.json ^
     -o result3.json

findstr /C:"assignment-coach" result3.json >nul
if errorlevel 1 (
    echo [FAILED] Test 3
    set /a FAILED+=1
) else (
    echo [PASSED] Test 3 - Advanced Database
    set /a PASSED+=1
)
del test3.json result3.json
echo.

REM ======================================================================
REM Test 4: Intermediate Data Science
REM ======================================================================
echo ======================================================================
echo [Test 4/8] Intermediate Data Science
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_104\",\"assignment_title\":\"Customer Churn Prediction\",\"assignment_description\":\"Analyze customer dataset to predict churn using ML models\",\"subject\":\"Data Science\",\"deadline\":\"2025-12-05\",\"difficulty\":\"Intermediate\",\"student_profile\":{\"learning_style\":\"hands-on\",\"progress\":0.6,\"skills\":[\"Python\",\"statistics\"],\"weaknesses\":[\"machine learning\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test4.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test4.json ^
     -o result4.json

findstr /C:"assignment-coach" result4.json >nul
if errorlevel 1 (
    echo [FAILED] Test 4
    set /a FAILED+=1
) else (
    echo [PASSED] Test 4 - Intermediate Data Science
    set /a PASSED+=1
)
del test4.json result4.json
echo.

REM ======================================================================
REM Test 5: Beginner Mobile App Design
REM ======================================================================
echo ======================================================================
echo [Test 5/8] Beginner Mobile App Design
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_105\",\"assignment_title\":\"Fitness Tracking App Design\",\"assignment_description\":\"Create wireframes and mockups for a mobile fitness app\",\"subject\":\"Mobile App Design\",\"deadline\":\"2025-11-30\",\"difficulty\":\"Beginner\",\"student_profile\":{\"learning_style\":\"visual\",\"progress\":0.1,\"skills\":[\"creativity\"],\"weaknesses\":[\"design tools\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test5.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test5.json ^
     -o result5.json

findstr /C:"assignment-coach" result5.json >nul
if errorlevel 1 (
    echo [FAILED] Test 5
    set /a FAILED+=1
) else (
    echo [PASSED] Test 5 - Beginner Mobile Design
    set /a PASSED+=1
)
del test5.json result5.json
echo.

REM ======================================================================
REM Test 6: Advanced Cybersecurity
REM ======================================================================
echo ======================================================================
echo [Test 6/8] Advanced Cybersecurity
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_106\",\"assignment_title\":\"Network Security Audit\",\"assignment_description\":\"Conduct security audit and penetration testing of test network\",\"subject\":\"Cybersecurity\",\"deadline\":\"2025-12-18\",\"difficulty\":\"Advanced\",\"student_profile\":{\"learning_style\":\"hands-on\",\"progress\":0.3,\"skills\":[\"networking\"],\"weaknesses\":[\"documentation\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test6.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test6.json ^
     -o result6.json

findstr /C:"assignment-coach" result6.json >nul
if errorlevel 1 (
    echo [FAILED] Test 6
    set /a FAILED+=1
) else (
    echo [PASSED] Test 6 - Advanced Cybersecurity
    set /a PASSED+=1
)
del test6.json result6.json
echo.

REM ======================================================================
REM Test 7: Intermediate AI/ML
REM ======================================================================
echo ======================================================================
echo [Test 7/8] Intermediate AI/ML
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_107\",\"assignment_title\":\"Image Classification CNN\",\"assignment_description\":\"Build CNN model to classify CIFAR-10 images\",\"subject\":\"Artificial Intelligence\",\"deadline\":\"2025-12-12\",\"difficulty\":\"Intermediate\",\"student_profile\":{\"learning_style\":\"mixed\",\"progress\":0.35,\"skills\":[\"Python\"],\"weaknesses\":[\"deep learning\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test7.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test7.json ^
     -o result7.json

findstr /C:"assignment-coach" result7.json >nul
if errorlevel 1 (
    echo [FAILED] Test 7
    set /a FAILED+=1
) else (
    echo [PASSED] Test 7 - Intermediate AI/ML
    set /a PASSED+=1
)
del test7.json result7.json
echo.

REM ======================================================================
REM Test 8: Beginner Software Testing
REM ======================================================================
echo ======================================================================
echo [Test 8/8] Beginner Software Testing
echo ======================================================================

(
echo {
echo   "agentId": "assignment-coach",
echo   "request": "{\"agent_name\":\"assignment_coach_agent\",\"intent\":\"generate_assignment_guidance\",\"payload\":{\"student_id\":\"stu_108\",\"assignment_title\":\"Library Management Test Plan\",\"assignment_description\":\"Create comprehensive test plan for library management system\",\"subject\":\"Software Testing\",\"deadline\":\"2025-11-28\",\"difficulty\":\"Beginner\",\"student_profile\":{\"learning_style\":\"reading\",\"progress\":0.5,\"skills\":[\"documentation\"],\"weaknesses\":[\"automation\"]}}}",
echo   "priority": 1,
echo   "autoRoute": false
echo }
) > test8.json

curl -s -X POST "http://localhost:8000/api/supervisor/request" ^
     -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d @test8.json ^
     -o result8.json

findstr /C:"assignment-coach" result8.json >nul
if errorlevel 1 (
    echo [FAILED] Test 8
    set /a FAILED+=1
) else (
    echo [PASSED] Test 8 - Beginner Testing
    set /a PASSED+=1
)
del test8.json result8.json
echo.

REM ======================================================================
REM Final Summary
REM ======================================================================
echo ======================================================================
echo    TEST SUMMARY
echo ======================================================================
echo Total Tests: 8
echo Passed: %PASSED%
echo Failed: %FAILED%
echo ======================================================================

if %FAILED% EQU 0 (
    echo [SUCCESS] All tests passed!
    exit /b 0
) else (
    echo [WARNING] Some tests failed
    exit /b 1
)
