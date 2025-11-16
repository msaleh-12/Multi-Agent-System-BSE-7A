@echo off
echo Testing Multi-Agent System API...
echo.
echo This script will:
echo 1. Check if services are running
echo 2. Login to get a token
echo 3. Send a test request to the supervisor
echo.
pause

python tests\integration_test.py

pause

