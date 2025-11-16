from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import uvicorn
import os
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import uuid
import json
from fastapi import Request

from .services.assessment_service import (
    generate_questions_by_type
)
from .services.rag_service import RAGService
from .services.pdf_service import generate_assessment_pdf
from .models import (
    AssessmentGenerationRequest,
    AssessmentResponse,
    QuestionResponse,
    RAGSearchRequest,
    RAGSearchResponse,
)
from shared.models import TaskEnvelope, CompletionReport

app = FastAPI(
    title="Assessment Generation Agent",
    description="A multi-agent system designed to assist university teachers by automating the generation of assessments (quizzes, assignments, exams). The system uses specialized AI agents to generate MCQs, short questions, and long questions based on the specified structure, difficulty levels",
    version="1.0.0"
)

# Global RAG service instance
rag_service = RAGService()

# Temporary directory for uploaded PDFs
UPLOAD_DIR = Path(tempfile.gettempdir()) / "assessment_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Output directory for generated PDFs
OUTPUT_DIR = Path(tempfile.gettempdir()) / "assessment_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_type": "exam readiness",
        "capabilities": ["quiz", "assignment", "examination", "rag", "pdf_export"],
        "rag_documents_loaded": rag_service.get_document_count()
    }


@app.post('/process', response_model=CompletionReport)
async def process_task(req: Request):
    """
    Process task from supervisor.
    Accepts TaskEnvelope and returns CompletionReport.
    
    Expected in task.parameters (RequestPayload format):
    {
        "agentId": "assessment-agent",
        "request": "user's natural language request",
        "priority": 1,
        "modelOverride": null,
        "autoRoute": false,
        "subject": "Python Programming",
        "assessment_type": "quiz",
        "difficulty": "easy",
        "question_count": 3,
        "type_counts": {"mcq": 3}
    }
    """
    try:
        body = await req.json()
        task_envelope = TaskEnvelope(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Extract parameters - supervisor sends RequestPayload in task.parameters
    params = task_envelope.task.parameters
    
    # Check if this is an assessment generation request
    # Parameters can come directly or nested
    assessment_params = params.get("assessment_params", params)
    
    # Validate required parameters for assessment generation
    required_fields = ["subject", "assessment_type", "difficulty", "question_count", "type_counts"]
    missing = [f for f in required_fields if f not in assessment_params]
    
    if missing:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssessmentGenerationAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": f"Missing required parameters: {', '.join(missing)}"}
        )

    try:
        # Validate type counts sum
        type_counts = assessment_params["type_counts"]
        question_count = assessment_params["question_count"]
        total_requested = sum(type_counts.values())
        
        if total_requested != question_count:
            return CompletionReport(
                message_id=str(uuid.uuid4()),
                sender="AssessmentGenerationAgent",
                recipient=task_envelope.sender,
                related_message_id=task_envelope.message_id,
                status="FAILURE",
                results={
                    "error": f"Sum of type_counts ({total_requested}) must equal question_count ({question_count})"
                }
            )
        
        # Build RAG context if requested
        rag_context = assessment_params.get("rag_context")
        if assessment_params.get("use_rag") and rag_service.get_document_count() > 0:
            results = rag_service.search(assessment_params["subject"], k=assessment_params.get("rag_top_k", 6))
            context_text = "\n\n".join([r.content for r in results])
            rag_max_chars = assessment_params.get("rag_max_chars", 4000)
            if len(context_text) > rag_max_chars:
                context_text = context_text[:rag_max_chars] + "\n[truncated]"
            rag_context = context_text
        
        # Generate questions using existing service
        all_questions, type_errors = generate_questions_by_type(
            subject=assessment_params["subject"],
            assessment_type=assessment_params["assessment_type"],
            difficulty=assessment_params["difficulty"],
            type_counts=type_counts,
            allow_latex=assessment_params.get("allow_latex", True),
            rag_context=rag_context,
            pdf_paths=None,
            rag_top_k=assessment_params.get("rag_top_k", 6),
            rag_max_chars=assessment_params.get("rag_max_chars", 4000),
        )
        
        # Check for generation errors
        errors = [f"{t}: {e}" for t, e in type_errors.items() if e]
        if errors:
            return CompletionReport(
                message_id=str(uuid.uuid4()),
                sender="AssessmentGenerationAgent",
                recipient=task_envelope.sender,
                related_message_id=task_envelope.message_id,
                status="FAILURE",
                results={"error": "; ".join(errors)}
            )
        
        # Build assessment response
        assessment = {
            "title": f"{assessment_params['subject']} — {assessment_params['assessment_type'].capitalize()} ({assessment_params['difficulty'].capitalize()})",
            "description": f"Auto-generated {assessment_params['assessment_type']} ({assessment_params['difficulty']}) for {assessment_params['subject']}",
            "assessment_type": assessment_params["assessment_type"],
            "subject": assessment_params["subject"],
            "difficulty": assessment_params["difficulty"],
            "total_questions": len(all_questions),
            "questions": all_questions,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "created_by": assessment_params.get("created_by", "supervisor"),
                "allow_latex": assessment_params.get("allow_latex", True),
                "used_rag": bool(rag_context),
                "type_distribution": {k: v for k, v in type_counts.items() if v > 0}
            }
        }
        
        # Format output similar to gemini_wrapper
        output = f"Generated assessment: {assessment['title']}\n"
        output += f"Total questions: {assessment['total_questions']}\n"
        output += f"Type distribution: {assessment['metadata']['type_distribution']}"
        
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssessmentGenerationAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="SUCCESS",
            results={
                "output": output,
                "assessment": assessment,
                "cached": False
            }
        )
        
    except Exception as e:
        return CompletionReport(
            message_id=str(uuid.uuid4()),
            sender="AssessmentGenerationAgent",
            recipient=task_envelope.sender,
            related_message_id=task_envelope.message_id,
            status="FAILURE",
            results={"error": f"Assessment generation failed: {str(e)}"}
        )


@app.post("/generate", response_model=AssessmentResponse)
async def generate_assessment(request: AssessmentGenerationRequest):
    """
    Generate an assessment based on the provided parameters.
    
    Supports:
    - Multiple question types (mcq, short_text, essay, coding, math)
    - Multiple assessment types (quiz, exam, assignment)
    - RAG context from uploaded PDFs
    - LaTeX support for mathematical notation
    """
    try:
        # Validate type counts
        total_requested = sum(request.type_counts.values())
        if total_requested != request.question_count:
            raise HTTPException(
                status_code=400,
                detail=f"Sum of type_counts ({total_requested}) must equal question_count ({request.question_count})"
            )
        
        # Build RAG context if PDF paths provided
        rag_context = request.rag_context
        if request.pdf_paths:
            results = rag_service.search(request.subject, k=request.rag_top_k)
            context_text = "\n\n".join([r.content for r in results])
            if len(context_text) > request.rag_max_chars:
                context_text = context_text[:request.rag_max_chars] + "\n[truncated]"
            rag_context = context_text
        
        # Generate questions
        all_questions, type_errors = generate_questions_by_type(
            subject=request.subject,
            assessment_type=request.assessment_type,
            difficulty=request.difficulty,
            type_counts=request.type_counts,
            allow_latex=request.allow_latex,
            rag_context=rag_context,
            pdf_paths=None,  # Already handled above
            rag_top_k=request.rag_top_k,
            rag_max_chars=request.rag_max_chars,
        )
        
        # Check for errors
        errors = [f"{t}: {e}" for t, e in type_errors.items() if e]
        if errors:
            raise HTTPException(status_code=500, detail="; ".join(errors))
        
        # Validate total count
        if len(all_questions) != request.question_count:
            raise HTTPException(
                status_code=500,
                detail=f"Expected {request.question_count} questions, got {len(all_questions)}"
            )
        
        # Convert to response format
        questions = [QuestionResponse(**q) for q in all_questions]
        
        return AssessmentResponse(
            title=f"{request.subject} — {request.assessment_type.capitalize()} ({request.difficulty.capitalize()})",
            description=f"Auto-generated {request.assessment_type} ({request.difficulty}) for {request.subject}",
            assessment_type=request.assessment_type,
            subject=request.subject,
            difficulty=request.difficulty,
            total_questions=len(questions),
            questions=questions,
            created_at=datetime.utcnow(),
            metadata={
                "created_by": request.created_by,
                "allow_latex": request.allow_latex,
                "used_rag": bool(rag_context),
                "type_distribution": {k: v for k, v in request.type_counts.items() if v > 0}
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment generation failed: {str(e)}")


@app.post("/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload PDF files for RAG processing.
    Returns the paths to the uploaded files.
    """
    try:
        uploaded_paths = []
        
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            # Save file
            file_path = UPLOAD_DIR / f"{datetime.utcnow().timestamp()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_paths.append(str(file_path))
        
        # Load PDFs into RAG service
        rag_service.load_pdfs(uploaded_paths)
        
        return {
            "message": f"Successfully uploaded and processed {len(files)} PDF(s)",
            "paths": uploaded_paths,
            "total_chunks": rag_service.get_document_count()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")


@app.post("/rag/search", response_model=RAGSearchResponse)
async def search_rag(request: RAGSearchRequest):
    """
    Search the RAG knowledge base for relevant content.
    """
    try:
        if rag_service.get_document_count() == 0:
            raise HTTPException(status_code=400, detail="No documents have been loaded yet")
        
        results = rag_service.search(request.query, k=request.top_k)
        
        return RAGSearchResponse(
            query=request.query,
            results=[
                {
                    "content": r.content,
                    "score": float(r.score) if r.score is not None else None,  # Convert numpy to Python float
                    "metadata": r.metadata or {}
                }
                for r in results
            ],
            total_documents=rag_service.get_document_count()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")


@app.post("/export-pdf")
async def export_assessment_pdf(assessment: AssessmentResponse):
    """
    Generate and download an assessment as a PDF.
    """
    try:
        # Generate PDF
        output_path = OUTPUT_DIR / f"assessment_{datetime.utcnow().timestamp()}.pdf"
        generate_assessment_pdf(assessment.dict(), str(output_path))
        
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=f"{assessment.title.replace(' ', '_')}.pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.delete("/rag/clear")
async def clear_rag():
    """Clear all documents from the RAG knowledge base."""
    try:
        rag_service.clear()
        
        # Clean up uploaded files
        for file in UPLOAD_DIR.glob("*"):
            file.unlink()
        
        return {
            "message": "RAG knowledge base cleared successfully",
            "documents_remaining": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear operation failed: {str(e)}")


@app.get("/rag/status")
async def rag_status():
    """Get the current status of the RAG knowledge base."""
    return {
        "documents_loaded": rag_service.get_document_count(),
        "upload_directory": str(UPLOAD_DIR),
        "status": "active" if rag_service.get_document_count() > 0 else "empty"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)