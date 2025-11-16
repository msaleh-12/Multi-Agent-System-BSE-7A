from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from typing import Dict, Any, List
from datetime import datetime


def generate_assessment_pdf(assessment_data: Dict[str, Any], output_path: str) -> None:
    """Generate a PDF document from assessment data"""
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='darkblue',
        spaceAfter=12
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph(assessment_data['title'], title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata
    story.append(Paragraph(f"<b>Subject:</b> {assessment_data['subject']}", styles['Normal']))
    story.append(Paragraph(f"<b>Type:</b> {assessment_data['assessment_type'].capitalize()}", styles['Normal']))
    story.append(Paragraph(f"<b>Difficulty:</b> {assessment_data['difficulty'].capitalize()}", styles['Normal']))
    story.append(Paragraph(f"<b>Total Questions:</b> {assessment_data['total_questions']}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Description
    if assessment_data.get('description'):
        story.append(Paragraph(assessment_data['description'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # Questions
    for idx, question in enumerate(assessment_data['questions'], 1):
        # Question header
        story.append(Paragraph(f"<b>Question {idx}</b> [{question['marks']} marks] ({question['difficulty'] or 'N/A'})", heading_style))
        
        # Question text
        story.append(Paragraph(question['question_text'], question_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Options for MCQ
        if question['question_type'] == 'mcq' and question['options']:
            for opt_idx, option in enumerate(question['options'], 1):
                letter_label = chr(64 + opt_idx)  # A, B, C, D
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{letter_label}. {option}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(story)