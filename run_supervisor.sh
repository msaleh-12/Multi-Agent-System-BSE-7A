#!/bin/bash
# run_supervisor.sh
echo "Starting Supervisor..."
uvicorn supervisor.main:app --host 0.0.0.0 --port 8000 --reload
