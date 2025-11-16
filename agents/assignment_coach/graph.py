"""
LangGraph workflow for Assignment Coach Agent.
"""
import logging
import json
import os
import yaml
from typing import Dict, Any, TypedDict, Annotated
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

from langgraph.graph import StateGraph, END
from agents.assignment_coach import ltm, tools

load_dotenv()

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

_logger = logging.getLogger(__name__)

ASSIGNMENT_COACH_CONFIG = config.get('assignment_coach', {})
API_KEY = os.getenv("GEMINI_API_KEY")
MODE = ASSIGNMENT_COACH_CONFIG.get("mode", "auto")

def _get_mode():
    """Determine if agent should run in mock or cloud mode."""
    if MODE == "cloud":
        return "cloud"
    if MODE == "mock":
        return "mock"
    # Auto mode
    if API_KEY:
        return "cloud"
    return "mock"

def _build_llm_prompt(payload: Dict[str, Any], tool_results: Dict[str, Any]) -> str:
    """Build prompt for LLM with tool results."""
    prompt = """You are the Assignment Coach Agent. Your job is to help students understand and complete assignments.

### TASK
Given the assignment payload and tool-generated information, generate a comprehensive response with:
- assignment summary (2-3 sentences)
- step-by-step task plan (use the provided task breakdown, but enhance it with more detail)
- resource recommendations (use the provided resources, but add more personalized suggestions)
- personalized feedback (based on student profile, progress, and deadline urgency)
- motivational message (keep it short, positive, and actionable)

### TOOL RESULTS
Time Estimate: {time_estimate}
Task Breakdown: {task_breakdown}
Resources: {resources}
Urgency Info: {urgency_info}

### ASSIGNMENT PAYLOAD
{payload}

### RULES
- Always output valid JSON only.
- Do not add extra text outside JSON.
- Enhance the tool results with your knowledge and personalization.
- Personalize responses based on student learning style, progress, skills, and weaknesses.
- Keep tone supportive and helpful.
- All timestamps must be in ISO-8601 UTC format.

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
""".format(
        time_estimate=json.dumps(tool_results.get("time_estimate", {}), indent=2),
        task_breakdown=json.dumps(tool_results.get("task_breakdown", []), indent=2),
        resources=json.dumps(tool_results.get("resources", []), indent=2),
        urgency_info=json.dumps(tool_results.get("urgency_info", {}), indent=2),
        payload=json.dumps(payload, indent=2)
    )
    return prompt

class AgentState(TypedDict):
    """State for the Assignment Coach Agent workflow."""
    payload: Dict[str, Any]
    intent: str
    ltm_result: str | None
    time_estimate: Dict[str, Any] | None
    task_breakdown: list | None
    resources: list | None
    urgency_info: Dict[str, Any] | None
    response: Dict[str, Any] | None
    final_output: str | None
    error: str | None

async def check_ltm(state: AgentState) -> AgentState:
    """Check Long-Term Memory for similar assignments."""
    _logger.info("Checking LTM for similar assignments...")
    payload = state["payload"]
    
    # Look up in vector DB
    ltm_result = None
    try:
        ltm_result = await ltm.lookup(payload)
    except Exception as e:
        _logger.error(f"Error checking LTM: {e}")
        ltm_result = None
    
    state["ltm_result"] = ltm_result
    return state

def use_tools(state: AgentState) -> AgentState:
    """Use tools to gather information and generate task breakdown."""
    _logger.info("Using tools to process assignment...")
    payload = state["payload"]
    student_profile = payload.get("student_profile", {})
    
    # Calculate time estimate
    difficulty = payload.get("difficulty", "Intermediate")
    assignment_type = "report"  # Could be extracted from description
    time_estimate = tools.calculate_time_estimate(difficulty, assignment_type)
    state["time_estimate"] = time_estimate
    
    # Generate task breakdown
    assignment_description = payload.get("assignment_description", "")
    progress = student_profile.get("progress", 0.0)
    total_hours = time_estimate["total_hours"]
    task_breakdown = tools.generate_task_breakdown(
        assignment_description,
        difficulty,
        progress,
        total_hours
    )
    state["task_breakdown"] = task_breakdown
    
    # Suggest resources
    learning_style = student_profile.get("learning_style", "visual")
    subject = payload.get("subject", "")
    topic = payload.get("assignment_title", "")
    resources = tools.suggest_resources_by_learning_style(
        learning_style,
        subject,
        topic
    )
    state["resources"] = resources
    
    # Calculate deadline urgency
    deadline = payload.get("deadline", "")
    if deadline:
        urgency_info = tools.calculate_deadline_urgency(deadline, progress)
        state["urgency_info"] = urgency_info
    
    return state

async def generate_response(state: AgentState) -> AgentState:
    """Generate the final JSON response using LLM or tools."""
    _logger.info("Generating final response...")
    
    # If we have cached result from LTM, use it
    if state.get("ltm_result"):
        try:
            response_data = json.loads(state["ltm_result"])
            state["response"] = response_data
            state["final_output"] = state["ltm_result"]
            return state
        except json.JSONDecodeError:
            _logger.warning("LTM result is not valid JSON, generating new response")
    
    # Determine if we should use LLM or tools
    mode = _get_mode()
    payload = state["payload"]
    
    if mode == "cloud" and API_KEY:
        # Use LLM to generate response with tool results
        try:
            _logger.info("Using LLM to generate response with tool results...")
            genai.configure(api_key=API_KEY)
            model_name = ASSIGNMENT_COACH_CONFIG.get("model", "gemini-2.5-flash")
            model = genai.GenerativeModel(model_name)
            
            # Prepare tool results
            tool_results = {
                "time_estimate": state.get("time_estimate"),
                "task_breakdown": state.get("task_breakdown"),
                "resources": state.get("resources"),
                "urgency_info": state.get("urgency_info")
            }
            
            # Build prompt with tool results
            prompt = _build_llm_prompt(payload, tool_results)
            
            # Call LLM
            response = await model.generate_content_async(prompt)
            response_text = response.text.strip()
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Validate and parse JSON
            try:
                response_data = json.loads(response_text)
                state["response"] = response_data
                state["final_output"] = response_text
                _logger.info("Successfully generated response using LLM")
                return state
            except json.JSONDecodeError as e:
                _logger.warning(f"LLM response is not valid JSON: {e}, falling back to tools")
                # Fall through to tools-based generation
        except Exception as e:
            _logger.error(f"Error calling LLM: {e}, falling back to tools")
            # Fall through to tools-based generation
    
    # Fallback: Generate response using tools (for mock mode or LLM errors)
    _logger.info("Generating response using tools...")
    student_profile = payload.get("student_profile", {})
    
    # Build response from tool outputs
    response = {
        "agent_name": "assignment_coach_agent",
        "status": "success",
        "response": {
            "assignment_summary": _generate_summary(payload),
            "task_plan": state.get("task_breakdown", []),
            "recommended_resources": state.get("resources", []),
            "feedback": _generate_feedback(payload, state),
            "motivation": _generate_motivation(payload),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    state["response"] = response
    state["final_output"] = json.dumps(response, indent=2)
    
    return state

async def save_to_ltm(state: AgentState) -> AgentState:
    """Save the response to Long-Term Memory."""
    _logger.info("Saving to LTM...")
    payload = state["payload"]
    output = state.get("final_output")
    
    if output:
        try:
            await ltm.save(payload, output)
        except Exception as e:
            _logger.error(f"Error saving to LTM: {e}")
    
    return state

def _generate_summary(payload: Dict[str, Any]) -> str:
    """Generate assignment summary."""
    title = payload.get("assignment_title", "Assignment")
    description = payload.get("assignment_description", "")
    subject = payload.get("subject", "")
    
    summary = f"This {subject} assignment titled '{title}' requires you to {description.lower()[:150]}... "
    summary += "Focus on understanding the core concepts and applying them systematically to complete the task successfully."
    
    return summary

def _generate_feedback(payload: Dict[str, Any], state: AgentState) -> str:
    """Generate personalized feedback."""
    student_profile = payload.get("student_profile", {})
    progress = student_profile.get("progress", 0.0)
    weaknesses = student_profile.get("weaknesses", [])
    skills = student_profile.get("skills", [])
    urgency_info = state.get("urgency_info", {})
    
    feedback = f"Based on your current progress ({int(progress*100)}%), "
    
    if urgency_info:
        urgency = urgency_info.get("urgency", "")
        days_remaining = urgency_info.get("days_remaining", 0)
        if urgency == "critical":
            feedback += f"you have {days_remaining} days remaining. Focus on completing high-priority tasks immediately. "
        elif urgency == "high":
            feedback += f"you have {days_remaining} days remaining. Maintain steady progress on your tasks. "
        else:
            feedback += f"you have {days_remaining} days remaining. Continue working at your current pace. "
    
    if "time management" in weaknesses:
        feedback += "Set specific deadlines for each task to improve time management. "
    
    if skills:
        feedback += f"Your strengths in {', '.join(skills)} will help you succeed. "
    
    return feedback

def _generate_motivation(payload: Dict[str, Any]) -> str:
    """Generate motivational message."""
    title = payload.get("assignment_title", "assignment")
    progress = payload.get("student_profile", {}).get("progress", 0.0)
    
    if progress < 0.3:
        motivation = f"You're just getting started with '{title}'. Every step forward counts - keep building momentum!"
    elif progress < 0.6:
        motivation = f"You're making great progress on '{title}'! You're halfway there - keep pushing forward!"
    else:
        motivation = f"You're in the final stretch for '{title}'! You've come so far - finish strong!"
    
    return motivation

def should_use_cached(state: AgentState) -> str:
    """Decide whether to use cached result or generate new."""
    if state.get("ltm_result"):
        return "use_cached"
    return "generate_new"

# Build the LangGraph workflow
def create_assignment_coach_graph():
    """Create and return the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("check_ltm", check_ltm)
    workflow.add_node("use_tools", use_tools)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("save_to_ltm", save_to_ltm)
    
    # Set entry point
    workflow.set_entry_point("check_ltm")
    
    # Add conditional edge after LTM check
    workflow.add_conditional_edges(
        "check_ltm",
        should_use_cached,
        {
            "use_cached": "generate_response",  # Skip tools and save if cached
            "generate_new": "use_tools"  # Use tools and generate new if not cached
        }
    )
    
    # Add edges
    workflow.add_edge("use_tools", "generate_response")
    
    # Conditional edge: only save if not cached
    def should_save(state: AgentState) -> str:
        """Decide whether to save to LTM or end."""
        if state.get("ltm_result"):
            return "end"  # Already in LTM, skip save
        return "save"  # New result, save it
    
    workflow.add_conditional_edges(
        "generate_response",
        should_save,
        {
            "save": "save_to_ltm",
            "end": END
        }
    )
    
    workflow.add_edge("save_to_ltm", END)
    
    return workflow.compile()

