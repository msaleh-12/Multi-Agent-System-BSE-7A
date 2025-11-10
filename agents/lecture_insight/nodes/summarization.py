"""
Summarization Node - Summarizes transcript and extracts keywords using Gemini
"""

import logging
import os
from typing import Dict, Any, List

_logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


async def summarize_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate summary and extract keywords from transcript.
    
    Args:
        state: Current workflow state with 'transcript'
        
    Returns:
        Updated state with 'summary' and 'keywords' fields
    """
    _logger.info("📝 Starting content summarization...")
    
    try:
        transcript = state.get("transcript", "")
        
        if not transcript:
            raise ValueError("No transcript available for summarization")
        
        if USE_MOCK:
            summary, keywords = await _mock_summarize(transcript)
        else:
            summary, keywords = await _real_summarize(transcript)
        
        state["summary"] = summary
        state["keywords"] = keywords
        
        _logger.info(f"✅ Summarization complete: {len(keywords)} keywords extracted")
        return state
        
    except Exception as e:
        _logger.error(f"❌ Summarization failed: {e}")
        state["error"] = f"Summarization error: {str(e)}"
        state["summary"] = ""
        state["keywords"] = []
        return state


async def _mock_summarize(transcript: str) -> tuple[str, List[str]]:
    """
    Mock summarization for testing without API calls.
    """
    _logger.info("🎭 Using MOCK summarization")
    
    # Detect topic from transcript
    transcript_lower = transcript.lower()
    
    if "machine learning" in transcript_lower or "supervised" in transcript_lower:
        summary = """
        This lecture introduces the fundamentals of machine learning, covering both 
        supervised and unsupervised learning approaches. Key topics include popular 
        algorithms like linear regression, decision trees, and neural networks. The 
        lecture also discusses critical concepts such as overfitting, underfitting, 
        and the bias-variance tradeoff. Model evaluation metrics including accuracy, 
        precision, recall, and F1 score are explained to help assess algorithm performance.
        """
        keywords = [
            "machine learning",
            "supervised learning",
            "unsupervised learning",
            "neural networks",
            "overfitting",
            "bias-variance tradeoff",
            "model evaluation",
            "classification",
            "regression"
        ]
    elif "python" in transcript_lower:
        summary = """
        This lecture covers Python programming fundamentals including variables, data types, 
        and control structures. Python's dynamic typing system and built-in data structures 
        (lists, tuples, dictionaries, sets) are explored. The session includes loops, 
        conditional statements, and function definitions including lambda functions and decorators.
        """
        keywords = [
            "python programming",
            "variables",
            "data types",
            "data structures",
            "functions",
            "loops",
            "conditional statements",
            "lambda functions"
        ]
    else:
        summary = """
        This lecture provides a comprehensive overview of key concepts and principles 
        in the subject matter. Historical context is reviewed to establish foundational 
        understanding. Complex topics are broken down with clear examples and analogies. 
        Practical case studies demonstrate real-world applications of the theories discussed.
        """
        keywords = [
            "fundamentals",
            "key concepts",
            "principles",
            "case studies",
            "practical examples",
            "theory",
            "applications"
        ]
    
    return summary.strip(), keywords


async def _real_summarize(transcript: str) -> tuple[str, List[str]]:
    """
    Real summarization using Google Gemini API.
    
    Requires: GEMINI_API_KEY environment variable
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set. Use USE_MOCK=true for testing.")
        
        _logger.info("🤖 Using Gemini for summarization")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate summary
        summary_prompt = f"""
        Summarize the following lecture transcript in 3-4 sentences. Focus on the main topics, 
        key concepts, and learning objectives:

        {transcript}
        
        Provide only the summary without any preamble.
        """
        
        summary_response = model.generate_content(summary_prompt)
        summary = summary_response.text.strip()
        
        # Extract keywords
        keywords_prompt = f"""
        Extract 5-10 key technical terms and concepts from this lecture transcript.
        Return ONLY a comma-separated list of keywords, nothing else:

        {transcript}
        """
        
        keywords_response = model.generate_content(keywords_prompt)
        keywords_text = keywords_response.text.strip()
        keywords = [k.strip() for k in keywords_text.split(",")]
        
        return summary, keywords
        
    except ImportError:
        _logger.error("Google Generative AI SDK not installed")
        raise
    except Exception as e:
        _logger.error(f"Gemini summarization failed: {e}")
        raise
