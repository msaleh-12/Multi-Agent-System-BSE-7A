"""
Gap Analysis Node - Identifies potential learning gaps from the lecture
"""

import logging
import os
from typing import Dict, Any, List

_logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


async def analyze_gaps(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify learning gaps and prerequisite knowledge from the lecture content.
    
    Args:
        state: Current workflow state with 'transcript', 'summary', 'keywords'
        
    Returns:
        Updated state with 'learning_gaps' field
    """
    _logger.info("🔍 Analyzing learning gaps...")
    
    try:
        transcript = state.get("transcript", "")
        keywords = state.get("keywords", [])
        
        if not transcript:
            raise ValueError("No transcript available for gap analysis")
        
        if USE_MOCK:
            learning_gaps = await _mock_analyze_gaps(transcript, keywords)
        else:
            learning_gaps = await _real_analyze_gaps(transcript, keywords)
        
        state["learning_gaps"] = learning_gaps
        
        _logger.info(f"✅ Gap analysis complete: {len(learning_gaps)} gaps identified")
        return state
        
    except Exception as e:
        _logger.error(f"❌ Gap analysis failed: {e}")
        state["error"] = f"Gap analysis error: {str(e)}"
        state["learning_gaps"] = []
        return state


async def _mock_analyze_gaps(transcript: str, keywords: List[str]) -> List[str]:
    """
    Mock gap analysis for testing without API calls.
    """
    _logger.info("🎭 Using MOCK gap analysis")
    
    transcript_lower = transcript.lower()
    
    if "machine learning" in transcript_lower:
        return [
            "Linear algebra fundamentals (vectors, matrices)",
            "Calculus basics (derivatives, gradients)",
            "Probability and statistics concepts",
            "Python programming for data manipulation"
        ]
    elif "python" in transcript_lower:
        return [
            "Basic computer science concepts",
            "Command line interface basics",
            "Text editor or IDE familiarity"
        ]
    else:
        return [
            "Background knowledge in the subject area",
            "Familiarity with core terminology",
            "Basic analytical thinking skills"
        ]


async def _real_analyze_gaps(transcript: str, keywords: List[str]) -> List[str]:
    """
    Real gap analysis using Google Gemini API.
    
    Requires: GEMINI_API_KEY environment variable
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set. Use USE_MOCK=true for testing.")
        
        _logger.info("🤖 Using Gemini for gap analysis")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Based on this lecture transcript and key topics, identify 3-5 prerequisite concepts 
        or skills that students should know before taking this lecture. Focus on foundational 
        knowledge that would help understanding.

        Keywords: {', '.join(keywords)}
        
        Transcript excerpt: {transcript[:1000]}...

        Return ONLY a numbered list of prerequisite topics, nothing else:
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse numbered list
        gaps = []
        for line in text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and clean up
                clean_line = line.lstrip('0123456789.-•) ').strip()
                if clean_line:
                    gaps.append(clean_line)
        
        return gaps[:5]  # Limit to 5 gaps
        
    except ImportError:
        _logger.error("Google Generative AI SDK not installed")
        raise
    except Exception as e:
        _logger.error(f"Gemini gap analysis failed: {e}")
        raise
