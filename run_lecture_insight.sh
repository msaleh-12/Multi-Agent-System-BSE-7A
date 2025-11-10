#!/bin/bash
# Run script for Lecture Insight Agent

export USE_MOCK=true
export LTM_DB_PATH="ltm_lecture_insight.db"

# Optional: Set real API keys when ready
# export GEMINI_API_KEY="your-key-here"
# export ASSEMBLYAI_API_KEY="your-key-here"
# export TAVILY_API_KEY="your-key-here"
# export YOUTUBE_API_KEY="your-key-here"

echo "🎓 Starting Lecture Insight Agent on port 5020..."
echo "   Mode: ${USE_MOCK:-false} mock"
echo "   LTM DB: ${LTM_DB_PATH:-ltm_lecture_insight.db}"
echo ""

uvicorn agents.lecture_insight.app:app --host 127.0.0.1 --port 5020 --reload
