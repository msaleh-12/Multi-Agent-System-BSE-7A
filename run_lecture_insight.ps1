# Run script for Lecture Insight Agent (Windows)

$env:USE_MOCK = "true"
$env:LTM_DB_PATH = "ltm_lecture_insight.db"

# Optional: Set real API keys when ready
# $env:GEMINI_API_KEY = "your-key-here"
# $env:ASSEMBLYAI_API_KEY = "your-key-here"
# $env:TAVILY_API_KEY = "your-key-here"
# $env:YOUTUBE_API_KEY = "your-key-here"

Write-Host "🎓 Starting Lecture Insight Agent on port 5020..." -ForegroundColor Green
Write-Host "   Mode: $env:USE_MOCK mock" -ForegroundColor Cyan
Write-Host "   LTM DB: $env:LTM_DB_PATH" -ForegroundColor Cyan
Write-Host ""

uvicorn agents.lecture_insight.app:app --host 127.0.0.1 --port 5020 --reload
