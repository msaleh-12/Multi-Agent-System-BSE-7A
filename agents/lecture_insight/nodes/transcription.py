"""
Transcription Node - Converts audio to text using AssemblyAI
"""

import logging
import os
from typing import Dict, Any

_logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


async def transcribe_audio(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transcribe audio input to text.
    
    Args:
        state: Current workflow state with audio_input
        
    Returns:
        Updated state with 'transcript' and 'audio_duration' fields
    """
    _logger.info("🎤 Starting audio transcription...")
    
    try:
        audio_input = state.get("audio_input", {})
        audio_data = audio_input.get("data")
        audio_format = audio_input.get("format")
        
        if not audio_data:
            raise ValueError("No audio data provided")
        
        if USE_MOCK:
            transcript, duration = await _mock_transcribe(audio_data, audio_format)
        else:
            transcript, duration = await _real_transcribe(audio_data, audio_format)
        
        state["transcript"] = transcript
        state["audio_duration"] = duration
        
        _logger.info(f"✅ Transcription complete: {len(transcript)} characters, {duration}s duration")
        return state
        
    except Exception as e:
        _logger.error(f"❌ Transcription failed: {e}")
        state["error"] = f"Transcription error: {str(e)}"
        state["transcript"] = ""
        state["audio_duration"] = 0
        return state


async def _mock_transcribe(audio_data: str, audio_format: str) -> tuple[str, float]:
    """
    Mock transcription for testing without API calls.
    
    Returns realistic transcript based on audio URL/data hint.
    """
    _logger.info("🎭 Using MOCK transcription")
    
    # Generate contextual mock based on URL
    if "ml" in audio_data.lower() or "machine" in audio_data.lower():
        transcript = """
        Welcome to Introduction to Machine Learning. Today we'll explore the fundamentals 
        of supervised and unsupervised learning. Machine learning is a subset of artificial 
        intelligence that enables systems to learn from data without being explicitly programmed.
        
        We'll start with supervised learning, where we have labeled training data. The algorithm 
        learns to map inputs to outputs based on example input-output pairs. Common algorithms 
        include linear regression, logistic regression, decision trees, and neural networks.
        
        Next, we'll discuss unsupervised learning, where we work with unlabeled data. The system 
        tries to find patterns and structure in the data. Clustering algorithms like K-means and 
        hierarchical clustering are popular examples.
        
        We'll also touch on key concepts like overfitting, underfitting, bias-variance tradeoff, 
        and model evaluation metrics such as accuracy, precision, recall, and F1 score.
        
        By the end of this lecture, you'll understand the core principles of machine learning 
        and be ready to apply these concepts to real-world problems.
        """
    elif "python" in audio_data.lower():
        transcript = """
        Hello everyone, welcome to Python Programming Basics. Python is a high-level, 
        interpreted programming language known for its simplicity and readability.
        
        Today we'll cover variables, data types, control structures, and functions. Python 
        uses dynamic typing, which means you don't need to declare variable types explicitly.
        
        We'll explore lists, tuples, dictionaries, and sets - Python's built-in data structures.
        Understanding these is crucial for effective Python programming.
        
        We'll also discuss loops, conditional statements, and how to write clean, Pythonic code.
        Finally, we'll look at functions, including lambda functions and decorators.
        """
    else:
        transcript = """
        Welcome to today's lecture. In this session, we will explore important concepts 
        and theories that form the foundation of this subject. We'll discuss key principles, 
        examine practical examples, and work through several case studies.
        
        First, we'll review the background and historical context. Understanding where these 
        ideas came from helps us appreciate their significance today.
        
        Then we'll dive into the main concepts, breaking down complex topics into manageable 
        pieces. I'll provide clear examples and analogies to help solidify your understanding.
        
        Throughout the lecture, feel free to take notes on the key points. We'll have a 
        Q&A session at the end to address any questions you might have.
        """
    
    # Simulate processing time and duration
    duration = len(transcript.split()) / 2.5  # ~150 words per minute
    
    return transcript.strip(), round(duration, 2)


async def _real_transcribe(audio_data: str, audio_format: str) -> tuple[str, float]:
    """
    Real transcription using AssemblyAI API.
    
    Requires: ASSEMBLYAI_API_KEY environment variable
    """
    try:
        import assemblyai as aai
        
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise ValueError("ASSEMBLYAI_API_KEY not set. Use USE_MOCK=true for testing.")
        
        _logger.info("🎙️ Using AssemblyAI for transcription")
        
        aai.settings.api_key = api_key
        transcriber = aai.Transcriber()
        
        # Handle different input types
        if audio_data.startswith("http"):
            # URL-based audio
            transcript_obj = transcriber.transcribe(audio_data)
        else:
            # Base64 or local file
            # TODO: Implement base64 decoding and temp file handling
            raise NotImplementedError("Base64 audio not yet supported")
        
        if transcript_obj.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript_obj.error}")
        
        transcript = transcript_obj.text
        duration = transcript_obj.audio_duration / 1000  # Convert ms to seconds
        
        return transcript, duration
        
    except ImportError:
        _logger.error("AssemblyAI SDK not installed. Install with: pip install assemblyai")
        raise
    except Exception as e:
        _logger.error(f"AssemblyAI transcription failed: {e}")
        raise
