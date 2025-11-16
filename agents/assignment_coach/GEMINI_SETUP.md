# Assignment Coach Agent - Gemini API Setup Guide

## 🔑 Getting Your Gemini API Key

### Step 1: Get API Key from Google AI Studio

1. **Visit Google AI Studio:**

   - Go to: https://aistudio.google.com/app/apikey
   - Or: https://makersuite.google.com/app/apikey

2. **Sign In:**

   - Use your Google account to sign in

3. **Create API Key:**
   - Click on "Get API Key" or "Create API Key"
   - Click "Create API key in new project" (or select existing project)
   - Copy the generated API key (it looks like: `AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Step 2: Configure Environment Variables

#### Option A: Create .env file in Assignment Coach directory (Recommended)

1. Navigate to the assignment coach directory:

   ```powershell
   cd agents\assignment_coach
   ```

2. Create `.env` file:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Edit `.env` and add your API key:
   ```env
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

#### Option B: Create .env file in root directory

1. Navigate to root directory:

   ```powershell
   cd C:\Code\SPM-Project\Multi-Agent-System-BSE-7A
   ```

2. Create `.env` file:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Edit `.env` and add your API key:
   ```env
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Step 3: Install Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install new dependencies
pip install google-generativeai python-dotenv

# Or install from requirements
pip install -r agents\assignment_coach\requirements.txt
```

### Step 4: Restart the Agent

```powershell
# Stop the current agent (Ctrl+C in the terminal)

# Restart with new configuration
uvicorn agents.assignment_coach.app:app --host 0.0.0.0 --port 5011 --reload
```

## ✅ Verify Installation

Run a test to verify Gemini API is working:

```powershell
python -c "import google.generativeai as genai; import os; from dotenv import load_dotenv; load_dotenv(); genai.configure(api_key=os.getenv('GEMINI_API_KEY')); model = genai.GenerativeModel('gemini-pro'); response = model.generate_content('Say hello'); print(response.text)"
```

## 🔄 How It Works

### With Gemini API (Smart Mode):

- ✅ Context-aware assignment summaries
- ✅ Specific task breakdowns tailored to the assignment
- ✅ Relevant resource recommendations
- ✅ Personalized feedback based on student profile
- ✅ Intelligent motivation messages

### Without Gemini API (Fallback Mode):

- ⚠️ Generic assignment summaries
- ⚠️ Template-based task plans
- ⚠️ Basic resource suggestions
- ⚠️ Rule-based feedback

## 📝 Example Usage

### Input (remains the same):

```json
{
  "agent_name": "assignment_coach_agent",
  "intent": "generate_assignment_guidance",
  "payload": {
    "student_id": "stu_001",
    "assignment_title": "AI Chatbot Design Report",
    "assignment_description": "Prepare a detailed report explaining the architecture and training process of a conversational AI chatbot.",
    "subject": "Artificial Intelligence",
    "deadline": "2025-10-20",
    "difficulty": "Intermediate",
    "student_profile": {
      "learning_style": "visual",
      "progress": 0.25,
      "skills": ["writing", "communication"],
      "weaknesses": ["time management"]
    }
  }
}
```

### Output (now AI-powered):

```json
{
  "agent_name": "assignment_coach_agent",
  "status": "success",
  "response": {
    "assignment_summary": "This report focuses on explaining the core components of a conversational AI chatbot including NLP pipeline, intent recognition, dialogue management, and training methodologies using real-world frameworks.",
    "task_plan": [
      {
        "step": 1,
        "task": "Research chatbot architectures (Rasa, Dialogflow, custom NLP) and document key components",
        "estimated_time": "2 days"
      },
      {
        "step": 2,
        "task": "Draft system architecture diagram showing NLP pipeline and dialogue flow",
        "estimated_time": "1 day"
      },
      {
        "step": 3,
        "task": "Write comprehensive report sections on training process and evaluation metrics",
        "estimated_time": "2 days"
      },
      {
        "step": 4,
        "task": "Review, add visuals, proofread, and finalize the document",
        "estimated_time": "1 day"
      }
    ],
    "recommended_resources": [
      {
        "type": "article",
        "title": "Rasa Open Source Framework Overview",
        "url": "https://rasa.com/docs/rasa/"
      },
      {
        "type": "video",
        "title": "Building a Chatbot with NLP - Complete Tutorial",
        "url": "https://www.youtube.com/watch?v=example"
      },
      {
        "type": "tool",
        "title": "Lucidchart for Architecture Diagrams",
        "url": "https://www.lucidchart.com"
      }
    ],
    "feedback": "You have completed 25% of your work. Focus on finishing your research phase by tomorrow to stay on track with your deadline.",
    "motivation": "Try time-blocking: dedicate specific 90-minute slots for research, then take 15-minute breaks. Use a Pomodoro timer to stay focused!",
    "timestamp": "2025-11-16T10:30:00Z"
  }
}
```

## 🚨 Troubleshooting

### Error: "GEMINI_API_KEY not found"

- Make sure `.env` file exists and contains the API key
- Restart the agent service after creating `.env`
- Check that the file is in the correct location

### Error: "API key invalid"

- Verify your API key is correct
- Ensure there are no extra spaces or quotes
- Generate a new API key if needed

### Agent still gives generic responses

- Check logs to confirm Gemini API is configured
- Look for "Gemini API configured successfully" in startup logs
- Verify no API errors in the console

## 📊 API Usage & Limits

- **Free Tier:** 60 requests per minute
- **Rate Limits:** Automatically handled with fallback
- **Cost:** Free for most use cases
- **Quotas:** Check at https://aistudio.google.com/app/apikey

## 🔒 Security Notes

- ⚠️ Never commit `.env` files to Git
- ✅ `.env` is already in `.gitignore`
- ✅ Use environment variables for production
- ✅ Rotate API keys periodically

## 🎯 Benefits of Gemini Integration

1. **Intelligent Summaries:** Context-aware understanding of assignment requirements
2. **Specific Tasks:** Tailored task breakdowns instead of generic steps
3. **Relevant Resources:** Real, useful resources based on the subject
4. **Personalized Feedback:** Student-specific guidance considering skills/weaknesses
5. **Smart Motivation:** Actionable tips addressing individual challenges

## 📞 Support

For issues:

1. Check the logs: Agent startup console
2. Verify API key: Test with the verification command
3. Review documentation: https://ai.google.dev/docs

---

**Note:** The agent works without Gemini API (fallback mode) but provides significantly better results with it configured.
