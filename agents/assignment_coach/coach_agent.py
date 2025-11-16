import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

_logger = logging.getLogger(__name__)

class AssignmentState(TypedDict):
    """State for the assignment coach agent"""
    input_data: Dict[str, Any]
    assignment_summary: str
    task_plan: list
    resources: list
    feedback: str
    motivation: str
    error: str

# Node functions for LangGraph
async def parse_input(state: AssignmentState) -> AssignmentState:
    """Parse and validate input data"""
    try:
        input_data = state["input_data"]
        payload = input_data.get("payload", {})
        
        if not payload.get("assignment_title"):
            state["error"] = "Missing assignment_title in payload"
        
        _logger.info(f"Parsed assignment: {payload.get('assignment_title')}")
        return state
    except Exception as e:
        state["error"] = f"Parse error: {str(e)}"
        return state

async def generate_summary(state: AssignmentState) -> AssignmentState:
    """Generate assignment summary"""
    try:
        payload = state["input_data"].get("payload", {})
        title = payload.get("assignment_title", "")
        description = payload.get("assignment_description", "")
        subject = payload.get("subject", "")
        
        # Simple summary generation
        state["assignment_summary"] = f"This assignment on {subject} focuses on {title}. {description[:100]}..."
        
        _logger.info("Generated assignment summary")
        return state
    except Exception as e:
        state["error"] = f"Summary error: {str(e)}"
        return state

async def create_task_plan(state: AssignmentState) -> AssignmentState:
    """Create a task breakdown plan"""
    try:
        payload = state["input_data"].get("payload", {})
        difficulty = payload.get("difficulty", "Intermediate")
        deadline_str = payload.get("deadline", "")
        
        # Calculate time estimates based on difficulty
        time_multiplier = {"Beginner": 1, "Intermediate": 1.5, "Advanced": 2}.get(difficulty, 1.5)
        
        # Generate task plan
        tasks = [
            {"step": 1, "task": "Research and gather relevant materials", "estimated_time": f"{int(2*time_multiplier)} days"},
            {"step": 2, "task": "Create outline and structure", "estimated_time": f"{int(1*time_multiplier)} days"},
            {"step": 3, "task": "Draft initial version", "estimated_time": f"{int(2*time_multiplier)} days"},
            {"step": 4, "task": "Review and finalize", "estimated_time": f"{int(1*time_multiplier)} days"}
        ]
        
        state["task_plan"] = tasks
        _logger.info("Created task plan")
        return state
    except Exception as e:
        state["error"] = f"Task plan error: {str(e)}"
        return state

async def recommend_resources(state: AssignmentState) -> AssignmentState:
    """Recommend learning resources"""
    try:
        payload = state["input_data"].get("payload", {})
        subject = payload.get("subject", "General")
        student_profile = payload.get("student_profile", {})
        learning_style = student_profile.get("learning_style", "mixed")
        
        # Generate resources based on learning style
        resources = []
        
        if learning_style in ["visual", "mixed"]:
            resources.append({
                "type": "video",
                "title": f"{subject} - Comprehensive Video Tutorial",
                "url": "https://www.youtube.com/results?search_query=" + subject.replace(" ", "+")
            })
        
        resources.append({
            "type": "article",
            "title": f"{subject} - Documentation and Guide",
            "url": "https://scholar.google.com/scholar?q=" + subject.replace(" ", "+")
        })
        
        resources.append({
            "type": "tool",
            "title": "Assignment Planning Template",
            "url": "https://docs.google.com/document"
        })
        
        state["resources"] = resources
        _logger.info("Generated resource recommendations")
        return state
    except Exception as e:
        state["error"] = f"Resource error: {str(e)}"
        return state

async def generate_feedback(state: AssignmentState) -> AssignmentState:
    """Generate personalized feedback and motivation"""
    try:
        payload = state["input_data"].get("payload", {})
        student_profile = payload.get("student_profile", {})
        progress = student_profile.get("progress", 0)
        weaknesses = student_profile.get("weaknesses", [])
        deadline_str = payload.get("deadline", "")
        
        # Generate feedback
        progress_pct = int(progress * 100)
        state["feedback"] = f"You have completed {progress_pct}% of your work. "
        
        if progress < 0.3:
            state["feedback"] += "Start with the research phase to build a strong foundation."
        elif progress < 0.7:
            state["feedback"] += "Good progress! Focus on drafting to stay on track."
        else:
            state["feedback"] += "Excellent! Complete final review before deadline."
        
        # Generate motivation
        if "time management" in weaknesses:
            state["motivation"] = "Break tasks into 25-minute focused sessions with short breaks. Use a timer to stay accountable!"
        elif "writing" in weaknesses:
            state["motivation"] = "Start with bullet points and expand gradually. Don't aim for perfection in the first draft!"
        else:
            state["motivation"] = "You're doing great! Maintain your momentum and stay consistent with daily progress."
        
        _logger.info("Generated feedback and motivation")
        return state
    except Exception as e:
        state["error"] = f"Feedback error: {str(e)}"
        return state

def should_continue(state: AssignmentState) -> str:
    """Decide whether to continue or end"""
    if state.get("error"):
        return "end"
    return "continue"

# Build LangGraph workflow
def create_workflow():
    """Create the LangGraph workflow"""
    workflow = StateGraph(AssignmentState)
    
    # Add nodes
    workflow.add_node("parse", parse_input)
    workflow.add_node("summary", generate_summary)
    workflow.add_node("tasks", create_task_plan)
    workflow.add_node("resources", recommend_resources)
    workflow.add_node("feedback", generate_feedback)
    
    # Define edges
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", "summary")
    workflow.add_edge("summary", "tasks")
    workflow.add_edge("tasks", "resources")
    workflow.add_edge("resources", "feedback")
    workflow.add_edge("feedback", END)
    
    return workflow.compile()

# Initialize workflow
graph = create_workflow()

async def process_assignment_request(input_request: str) -> Dict[str, Any]:
    """Main processing function using LangGraph"""
    try:
        # Parse input
        if isinstance(input_request, str):
            try:
                input_data = json.loads(input_request)
            except:
                input_data = {"payload": {"assignment_title": input_request}}
        else:
            input_data = input_request
        
        # Initialize state
        initial_state: AssignmentState = {
            "input_data": input_data,
            "assignment_summary": "",
            "task_plan": [],
            "resources": [],
            "feedback": "",
            "motivation": "",
            "error": ""
        }
        
        # Run the graph
        final_state = await graph.ainvoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            return {"error": final_state["error"]}
        
        # Build output in the required format
        output = {
            "agent_name": input_data.get("agent_name", "assignment_coach_agent"),
            "status": "success",
            "response": {
                "assignment_summary": final_state["assignment_summary"],
                "task_plan": final_state["task_plan"],
                "recommended_resources": final_state["resources"],
                "feedback": final_state["feedback"],
                "motivation": final_state["motivation"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        return {"output": json.dumps(output), "cached": False}
        
    except Exception as e:
        _logger.error(f"Error processing assignment request: {e}")
        return {"error": f"Processing failed: {str(e)}"}
