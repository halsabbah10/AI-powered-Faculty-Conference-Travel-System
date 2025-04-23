"""
Document service module.
Handles document processing, extraction and manipulation.
"""

import os
import PyPDF2
import docx
import logging
from io import BytesIO
import streamlit as st
from functools import lru_cache

def extract_text_from_file(file):
    """Extract text from uploaded PDF or Word documents"""
    try:
        if file.type == "application/pdf":
            # Handle PDF files
            pdf_reader = PyPDF2.PdfReader(BytesIO(file.getvalue()))
            return "\n".join([page.extract_text() for page in pdf_reader.pages])
        
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Handle Word documents
            doc = docx.Document(BytesIO(file.getvalue()))
            return "\n".join([para.text for para in doc.paragraphs])
        
        else:
            raise ValueError("Unsupported file format")
            
    except Exception as e:
        logging.error(f"Error extracting text from file: {str(e)}")
        raise

def validate_file(file, max_size_mb=10, allowed_types=None):
    """Validate file size and type"""
    if allowed_types is None:
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        
    if file is None:
        return False, "No file uploaded"
        
    # Check file type
    if file.type not in allowed_types:
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    if file.size > max_size_bytes:
        return False, f"File is too large. Maximum size allowed: {max_size_mb}MB"
        
    return True, "File is valid"

def save_uploaded_file(file, request_id, file_type):
    """Save uploaded file to database"""
    from app.database.connection import DatabaseManager
    
    try:
        file_data = file.getvalue()
        file_name = file.name
        file_size = len(file_data)
        
        # Insert file into database
        DatabaseManager.execute_query(
            """
            INSERT INTO uploadedfiles 
            (request_id, file_name, file_type, file_size, file_data, upload_date)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (request_id, file_name, file_type, file_size, file_data),
            fetch=False,
            commit=True
        )
        
        return True, "File saved successfully"
        
    except Exception as e:
        logging.error(f"Error saving uploaded file: {str(e)}")
        return False, f"Error saving file: {str(e)}"

def get_uploaded_file(request_id, file_type):
    """Retrieve uploaded file from database"""
    from app.database.connection import DatabaseManager
    
    try:
        result = DatabaseManager.execute_query(
            "SELECT * FROM uploadedfiles WHERE request_id = %s AND file_type = %s",
            (request_id, file_type)
        )
        
        if not result:
            return None
            
        return result[0]
        
    except Exception as e:
        logging.error(f"Error retrieving uploaded file: {str(e)}")
        return None

@lru_cache(maxsize=32)
def get_autofill(research_paper):
    """Extract conference details from research paper for auto-filling"""
    from app.services.ai_service import openai_client
    import json
    
    try:
        if not openai_client:
            return None
            
        # Extract text from research paper
        paper_text = extract_text_from_file(research_paper)
        
        prompt = f"""
        Extract conference submission details from this research paper:
        
        {paper_text[:4000]}
        
        Extract these specific details:
        1. Conference name (full name)
        2. Conference location/city
        3. Conference dates or year
        4. Research field/topic
        5. Authors and their affiliations
        
        Format your response as a JSON object with these keys: 
        conference_name, location, dates, field, authors
        If you cannot find a specific piece of information, use "Not found" as the value.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a research paper analyzer that extracts conference information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logging.error(f"Error in get_autofill: {str(e)}")
        return None

def convert_to_pdf(doc_content, output_file):
    """Convert document content to PDF format"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        
        # Create PDF document
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Format content for PDF
        content = []
        for line in doc_content.split('\n'):
            if line.strip():
                content.append(Paragraph(line, styles["Normal"]))
                
        # Build PDF
        doc.build(content)
        
        return True, "PDF created successfully"
        
    except Exception as e:
        logging.error(f"Error converting to PDF: {str(e)}")
        return False, f"Error creating PDF: {str(e)}"