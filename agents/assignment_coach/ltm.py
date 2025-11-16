import os
import logging
import json
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

_logger = logging.getLogger(__name__)

# Initialize embedding model
_embedding_model = None
_chroma_client = None
_collection = None

def get_embedding_model():
    """Lazy load embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _logger.info("Loading sentence transformer model for embeddings...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def get_chroma_client():
    """Initialize and return ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        db_path = os.path.join(os.getcwd(), "chroma_db_assignment_coach")
        _chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        _logger.info(f"Initialized ChromaDB client at {db_path}")
    return _chroma_client

def get_collection():
    """Get or create the collection for assignment coach LTM."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        try:
            _collection = client.get_collection(name="assignment_coach_ltm")
            _logger.info("Loaded existing assignment_coach_ltm collection")
        except Exception:
            _collection = client.create_collection(
                name="assignment_coach_ltm",
                metadata={"description": "Long-term memory for Assignment Coach Agent"}
            )
            _logger.info("Created new assignment_coach_ltm collection")
    return _collection

async def init_db():
    """Initialize the vector database."""
    try:
        get_collection()
        _logger.info("Assignment Coach LTM (Vector DB) initialized successfully")
    except Exception as e:
        _logger.error(f"Error initializing LTM: {e}")
        raise

def _create_query_text(payload: Dict[str, Any]) -> str:
    """Create a searchable text representation from payload."""
    # Extract key information for semantic search
    parts = []
    
    if "assignment_title" in payload:
        parts.append(f"Assignment: {payload['assignment_title']}")
    if "assignment_description" in payload:
        parts.append(f"Description: {payload['assignment_description']}")
    if "subject" in payload:
        parts.append(f"Subject: {payload['subject']}")
    if "difficulty" in payload:
        parts.append(f"Difficulty: {payload['difficulty']}")
    if "student_profile" in payload:
        profile = payload["student_profile"]
        if "learning_style" in profile:
            parts.append(f"Learning style: {profile['learning_style']}")
        if "skills" in profile:
            parts.append(f"Skills: {', '.join(profile['skills'])}")
        if "weaknesses" in profile:
            parts.append(f"Weaknesses: {', '.join(profile['weaknesses'])}")
    
    return " | ".join(parts)

async def lookup(payload: Dict[str, Any], similarity_threshold: float = 0.7) -> Optional[str]:
    """
    Look up similar assignments in LTM using semantic similarity.
    Returns the output if a similar assignment is found.
    """
    try:
        collection = get_collection()
        model = get_embedding_model()
        
        # Create query text from payload
        query_text = _create_query_text(payload)
        
        # Generate embedding for the query
        query_embedding = model.encode(query_text).tolist()
        
        # Search for similar assignments
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,  # Get top 3 similar results
            include=["documents", "metadatas", "distances"]
        )
        
        if results["ids"] and len(results["ids"][0]) > 0:
            # Check if the most similar result meets the threshold
            # ChromaDB returns distances (lower is more similar)
            # We'll convert distance to similarity (1 - normalized_distance)
            distances = results["distances"][0]
            if distances:
                # Normalize distance to similarity (assuming max distance is ~2.0)
                similarities = [1 - (d / 2.0) for d in distances]
                max_similarity = max(similarities)
                
                if max_similarity >= similarity_threshold:
                    # Get the most similar result
                    best_idx = similarities.index(max_similarity)
                    output_text = results["documents"][0][best_idx]
                    _logger.info(f"LTM cache hit with similarity {max_similarity:.3f}")
                    return output_text
                else:
                    _logger.info(f"Similar assignment found but similarity {max_similarity:.3f} below threshold {similarity_threshold}")
        
        return None
        
    except Exception as e:
        _logger.error(f"Error in LTM lookup: {e}")
        return None

async def save(payload: Dict[str, Any], output_text: str):
    """Save assignment payload and output to vector database."""
    try:
        collection = get_collection()
        model = get_embedding_model()
        
        # Create searchable text from payload
        query_text = _create_query_text(payload)
        
        # Generate embedding
        embedding = model.encode(query_text).tolist()
        
        # Create metadata
        metadata = {
            "assignment_title": payload.get("assignment_title", ""),
            "subject": payload.get("subject", ""),
            "difficulty": payload.get("difficulty", ""),
            "student_id": payload.get("student_id", ""),
        }
        
        # Generate unique ID from payload
        import hashlib
        payload_str = json.dumps(payload, sort_keys=True)
        doc_id = hashlib.sha256(payload_str.encode()).hexdigest()
        
        # Add to collection
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[output_text],
            metadatas=[metadata]
        )
        
        _logger.info(f"Saved to Assignment Coach LTM (Vector DB) with ID {doc_id[:8]}...")
        
    except Exception as e:
        _logger.error(f"Error saving to LTM: {e}")
        raise
