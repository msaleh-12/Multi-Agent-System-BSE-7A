import os
import logging
import json
import yaml
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from agents.assignment_coach.graph import create_assignment_coach_graph

load_dotenv()

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

_logger = logging.getLogger(__name__)

ASSIGNMENT_COACH_CONFIG = config.get('assignment_coach', {})
API_KEY = os.getenv("GEMINI_API_KEY")

MODE = ASSIGNMENT_COACH_CONFIG.get("mode", "auto")

def get_mode():
    """Determine if agent should run in mock or cloud mode."""
    if MODE == "cloud":
        return "cloud"
    if MODE == "mock":
        return "mock"
    # Auto mode
    if API_KEY:
        _logger.info("GEMINI_API_KEY found, running in 'cloud' mode.")
        genai.configure(api_key=API_KEY)
        return "cloud"
    _logger.warning("GEMINI_API_KEY not set, falling back to 'mock' mode.")
    return "mock"

def build_prompt(payload: Dict[str, Any]) -> str:
    """Build the prompt for the Assignment Coach Agent."""
    prompt = """You are the Assignment Coach Agent. Your job is to help students understand and complete assignments.

### TASK
Given the payload, generate:
- assignment summary
- step-by-step task plan
- resource recommendations
- personalized feedback
- motivational message

### RULES
- Always output valid JSON only.
- Do not add extra text outside JSON.
- Task plan steps must be realistic and sequential.
- Personalize responses based on student learning style, progress, skills, and weaknesses.
- Keep tone supportive and helpful.
- All timestamps must be in ISO-8601 UTC format.

### INPUT
{payload}

### OUTPUT FORMAT
{{
  "agent_name": "assignment_coach_agent",
  "status": "success",
  "response": {{
    "assignment_summary": "",
    "task_plan": [],
    "recommended_resources": [],
    "feedback": "",
    "motivation": "",
    "timestamp": ""
  }}
}}
""".format(payload=json.dumps(payload, indent=2))
    return prompt

def generate_mock_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a deterministic mock response for testing."""
    from agents.assignment_coach import tools
    
    student_profile = payload.get("student_profile", {})
    learning_style = student_profile.get("learning_style", "visual")
    progress = student_profile.get("progress", 0.0)
    skills = student_profile.get("skills", [])
    weaknesses = student_profile.get("weaknesses", [])
    
    assignment_title = payload.get("assignment_title", "Assignment")
    assignment_description = payload.get("assignment_description", "")
    difficulty = payload.get("difficulty", "Intermediate")
    deadline = payload.get("deadline", "")
    subject = payload.get("subject", "")
    
    # Use tools to generate response
    time_estimate = tools.calculate_time_estimate(difficulty, "report")
    task_breakdown = tools.generate_task_breakdown(
        assignment_description,
        difficulty,
        progress,
        time_estimate["total_hours"]
    )
    resources = tools.suggest_resources_by_learning_style(
        learning_style,
        subject,
        assignment_title
    )
    
    # Generate assignment summary
    summary = f"This assignment requires you to {assignment_description.lower()[:100]}... Focus on understanding the core concepts and applying them systematically."
    
    # Generate feedback
    feedback = f"Based on your progress ({int(progress*100)}%), focus on completing the next steps. "
    if "time management" in weaknesses:
        feedback += "Set specific deadlines for each task to improve time management. "
    feedback += f"Your strengths in {', '.join(skills)} will help you succeed."
    
    # Generate motivation
    motivation = f"You're making great progress! Keep pushing forward, and remember: every step brings you closer to completing '{assignment_title}'."
    
    return {
        "output": json.dumps({
            "agent_name": "assignment_coach_agent",
            "status": "success",
            "response": {
                "assignment_summary": summary,
                "task_plan": task_breakdown,
                "recommended_resources": resources,
                "feedback": feedback,
                "motivation": motivation,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }, indent=2),
        "mock": True
    }

async def generate_assignment_guidance(payload: Dict[str, Any], model_override: str = None) -> Dict[str, Any]:
    """
    Generate assignment guidance using LangGraph workflow.
    This is the main entry point that uses tools and LTM.
    """
    mode = get_mode()
    
    if mode == "mock":
        return generate_mock_response(payload)
    
    # Use LangGraph workflow for cloud mode
    try:
        # Create the graph
        graph = create_assignment_coach_graph()
        
        # Initial state
        initial_state = {
            "payload": payload,
            "intent": "generate_assignment_guidance",
            "ltm_result": None,
            "time_estimate": None,
            "task_breakdown": None,
            "resources": None,
            "urgency_info": None,
            "response": None,
            "final_output": None,
            "error": None
        }
        
        # Run the graph asynchronously
        result = await graph.ainvoke(initial_state)
        
        if result.get("error"):
            _logger.error(f"Error in workflow: {result['error']}")
            return {"error": result["error"]}
        
        output = result.get("final_output")
        if not output:
            # Fallback to LLM if workflow didn't produce output
            return await _generate_with_llm(payload, model_override)
        
        return {
            "output": output,
            "mock": False
        }
    
    except Exception as e:
        _logger.error(f"Error in LangGraph workflow: {e}")
        # Fallback to LLM or mock
        if mode == "cloud":
            return await _generate_with_llm(payload, model_override)
        else:
            return generate_mock_response(payload)

async def _generate_with_llm(payload: Dict[str, Any], model_override: str = None) -> Dict[str, Any]:
    """Fallback: Generate using LLM directly."""
    try:
        model_name = model_override or ASSIGNMENT_COACH_CONFIG.get("model", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        prompt = build_prompt(payload)
        response = await model.generate_content_async(prompt)
        
        # Try to parse JSON from response
        response_text = response.text.strip()
        
        # Extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Validate JSON
        try:
            json.loads(response_text)
        except json.JSONDecodeError:
            _logger.warning("Response is not valid JSON, using as-is")
        
        return {
            "output": response_text,
            "mock": False
        }
    
    except Exception as e:
        _logger.error(f"Error calling Google GenAI: {e}")
        # Final fallback to mock
        return generate_mock_response(payload)
