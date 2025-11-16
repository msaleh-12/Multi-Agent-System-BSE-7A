@echo off
echo Starting Gemini Wrapper...
uvicorn agents.gemini_wrapper.app:app --host 0.0.0.0 --port 5010 --reload

