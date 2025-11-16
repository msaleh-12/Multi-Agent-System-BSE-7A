"""
Tools for the Assignment Coach Agent.
Tools are functions that the agent can use to perform specific tasks.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

_logger = logging.getLogger(__name__)

def calculate_time_estimate(difficulty: str, assignment_type: str = "report") -> Dict[str, Any]:
    """
    Tool to calculate time estimates based on assignment difficulty and type.
    
    Args:
        difficulty: "Beginner", "Intermediate", or "Advanced"
        assignment_type: Type of assignment (report, project, essay, etc.)
    
    Returns:
        Dictionary with time estimates
    """
    base_hours = {
        "Beginner": 8,
        "Intermediate": 16,
        "Advanced": 24
    }
    
    type_multipliers = {
        "report": 1.0,
        "project": 1.5,
        "essay": 0.8,
        "presentation": 0.7,
        "lab": 1.2
    }
    
    base = base_hours.get(difficulty, 16)
    multiplier = type_multipliers.get(assignment_type.lower(), 1.0)
    total_hours = base * multiplier
    
    return {
        "total_hours": total_hours,
        "research_hours": total_hours * 0.3,
        "writing_hours": total_hours * 0.4,
        "review_hours": total_hours * 0.2,
        "formatting_hours": total_hours * 0.1
    }

def suggest_resources_by_learning_style(
    learning_style: str,
    subject: str,
    topic: str
) -> List[Dict[str, str]]:
    """
    Tool to suggest resources based on learning style.
    
    Args:
        learning_style: "visual", "auditory", "reading", "kinesthetic"
        subject: Subject area
        topic: Specific topic
    
    Returns:
        List of recommended resources
    """
    resources = []
    
    if learning_style == "visual":
        resources = [
            {
                "type": "video",
                "title": f"{subject} Visual Guide: {topic}",
                "url": f"https://example.com/videos/{subject.lower()}/{topic.lower()}",
                "description": "Video tutorial with diagrams and visual explanations"
            },
            {
                "type": "diagram",
                "title": f"{topic} Architecture Diagrams",
                "url": f"https://example.com/diagrams/{topic.lower()}",
                "description": "Visual diagrams and flowcharts"
            },
            {
                "type": "infographic",
                "title": f"{subject} Quick Reference",
                "url": f"https://example.com/infographics/{subject.lower()}",
                "description": "Visual summary and key concepts"
            }
        ]
    elif learning_style == "auditory":
        resources = [
            {
                "type": "podcast",
                "title": f"{subject} Podcast Series",
                "url": f"https://example.com/podcasts/{subject.lower()}",
                "description": "Audio lectures and discussions"
            },
            {
                "type": "audio_book",
                "title": f"{topic} Audio Guide",
                "url": f"https://example.com/audio/{topic.lower()}",
                "description": "Narrated explanations"
            }
        ]
    elif learning_style in ["reading", "writing"]:
        resources = [
            {
                "type": "article",
                "title": f"{subject} Documentation",
                "url": f"https://example.com/docs/{subject.lower()}",
                "description": "Comprehensive written documentation"
            },
            {
                "type": "pdf",
                "title": f"{topic} Research Paper",
                "url": f"https://example.com/papers/{topic.lower()}.pdf",
                "description": "Academic papers and research"
            },
            {
                "type": "book",
                "title": f"{subject} Textbook Chapter",
                "url": f"https://example.com/books/{subject.lower()}",
                "description": "Detailed written explanations"
            }
        ]
    else:  # kinesthetic
        resources = [
            {
                "type": "interactive",
                "title": f"{topic} Hands-on Lab",
                "url": f"https://example.com/labs/{topic.lower()}",
                "description": "Interactive exercises and labs"
            },
            {
                "type": "tutorial",
                "title": f"{subject} Step-by-step Guide",
                "url": f"https://example.com/tutorials/{subject.lower()}",
                "description": "Practical walkthrough"
            },
            {
                "type": "workshop",
                "title": f"{topic} Workshop",
                "url": f"https://example.com/workshops/{topic.lower()}",
                "description": "Hands-on practice session"
            }
        ]
    
    return resources

def generate_task_breakdown(
    assignment_description: str,
    difficulty: str,
    progress: float,
    total_hours: float
) -> List[Dict[str, Any]]:
    """
    Tool to generate a task breakdown based on assignment details.
    
    Args:
        assignment_description: Description of the assignment
        difficulty: Difficulty level
        progress: Current progress (0.0 to 1.0)
        total_hours: Total estimated hours
    
    Returns:
        List of task steps
    """
    # Determine which phase we're in
    if progress < 0.3:
        phase = "initial"
        steps = [
            {"step": 1, "task": "Research and gather resources", "estimated_hours": total_hours * 0.3, "priority": "high"},
            {"step": 2, "task": "Create outline and structure", "estimated_hours": total_hours * 0.15, "priority": "high"},
            {"step": 3, "task": "Write introduction and background", "estimated_hours": total_hours * 0.2, "priority": "medium"},
        ]
    elif progress < 0.6:
        phase = "middle"
        steps = [
            {"step": 1, "task": "Complete main content sections", "estimated_hours": total_hours * 0.3, "priority": "high"},
            {"step": 2, "task": "Review and revise content", "estimated_hours": total_hours * 0.2, "priority": "high"},
            {"step": 3, "task": "Add supporting evidence and examples", "estimated_hours": total_hours * 0.15, "priority": "medium"},
        ]
    else:
        phase = "final"
        steps = [
            {"step": 1, "task": "Final review and proofreading", "estimated_hours": total_hours * 0.2, "priority": "high"},
            {"step": 2, "task": "Format document and add citations", "estimated_hours": total_hours * 0.1, "priority": "medium"},
            {"step": 3, "task": "Submit assignment", "estimated_hours": 0.5, "priority": "high"},
        ]
    
    return steps

def calculate_deadline_urgency(deadline: str, progress: float) -> Dict[str, Any]:
    """
    Tool to calculate deadline urgency and provide time management advice.
    
    Args:
        deadline: Deadline date in YYYY-MM-DD format
        progress: Current progress (0.0 to 1.0)
    
    Returns:
        Dictionary with urgency information
    """
    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        today = datetime.now()
        days_remaining = (deadline_date - today).days
        
        if days_remaining < 0:
            urgency = "overdue"
            urgency_level = 5
        elif days_remaining < 3:
            urgency = "critical"
            urgency_level = 4
        elif days_remaining < 7:
            urgency = "high"
            urgency_level = 3
        elif days_remaining < 14:
            urgency = "moderate"
            urgency_level = 2
        else:
            urgency = "low"
            urgency_level = 1
        
        # Calculate if progress is on track
        expected_progress = 1.0 - (days_remaining / 30.0) if days_remaining > 0 else 1.0
        on_track = progress >= expected_progress * 0.8
        
        return {
            "days_remaining": days_remaining,
            "urgency": urgency,
            "urgency_level": urgency_level,
            "on_track": on_track,
            "expected_progress": max(0, min(1, expected_progress)),
            "current_progress": progress
        }
    except Exception as e:
        _logger.error(f"Error calculating deadline urgency: {e}")
        return {
            "days_remaining": None,
            "urgency": "unknown",
            "urgency_level": 0,
            "on_track": False
        }

# Export all tools
AVAILABLE_TOOLS = {
    "calculate_time_estimate": calculate_time_estimate,
    "suggest_resources_by_learning_style": suggest_resources_by_learning_style,
    "generate_task_breakdown": generate_task_breakdown,
    "calculate_deadline_urgency": calculate_deadline_urgency,
}

