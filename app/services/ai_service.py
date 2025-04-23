"""
AI service integration module.
Handles interactions with OpenAI and Google Gemini APIs.
"""

import os
import logging
from functools import lru_cache
import json
from openai import OpenAI
from google import genai
from google.genai import types
import streamlit as st

# Initialize AI clients
def initialize_ai_services():
    """Initialize connections to AI services"""
    # OpenAI setup
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logging.info("OpenAI API initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing OpenAI API: {str(e)}")
        openai_client = None
    
    # Google Gemini setup
    try:
        genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
        logging.info("Google Gemini API initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing Google Gemini API: {str(e)}")
    
    return openai_client

# Initialize OpenAI client
openai_client = initialize_ai_services()

@lru_cache(maxsize=32)
def validate_with_gpt(conference_name, research_paper_text, acceptance_letter_text, selected_index, conference_url=None):
    """Validate conference documents using GPT"""
    try:
        # Check if OpenAI client is available
        if not openai_client:
            return {
                "valid": False,
                "error": "OpenAI service is not available",
                "details": "Please check your API key and try again later."
            }
            
        # URL-based index check
        url_index_match, found_indexes = (False, [])
        if conference_url:
            url_index_match, found_indexes = extract_index_from_url(conference_url, selected_index)
            
        # Check for organizational naming convention matches
        org_in_name = any(org in conference_name.upper() for org in ["ACM", "IEEE"])
        org_match = selected_index.upper() in conference_name.upper()
            
        # Create prompt for GPT
        prompt = f"""
        Validate these conference submission elements:
        
        Conference name: {conference_name}
        Selected index: {selected_index}
        
        Research paper extract:
        {research_paper_text[:1000]}...
        
        Acceptance letter extract:
        {acceptance_letter_text[:1000]}...
        
        Additional context:
        - URL index match: {url_index_match} (found: {found_indexes})
        - Organization in name: {org_in_name}
        - Organization matches index: {org_match}
        
        Determine:
        1. Is this a legitimate academic conference? (consider conference name, index)
        2. Does the research paper content match the conference topic?
        3. Is the acceptance letter authentic and related to this paper and conference?
        
        First provide detailed observations about each document, then a final verdict.
        Format your response as a JSON object with these keys:
        {
            "legitimate_conference": true/false,
            "paper_conference_match": true/false,
            "authentic_acceptance": true/false,
            "observations": "",
            "valid": true/false,
            "recommendation": ""
        }
        """
        
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a conference validation expert who verifies academic integrity."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Add additional verification info
        result["url_index_match"] = url_index_match
        result["org_in_name"] = org_in_name
        result["org_match"] = org_match
        
        return result
        
    except Exception as e:
        logging.error(f"Error in validate_with_gpt: {str(e)}")
        return {
            "valid": False,
            "error": "Validation service error",
            "details": str(e)
        }

@lru_cache(maxsize=32)
def extract_index_from_url(url, selected_index):
    """Extract and verify index information from conference URL"""
    url = url.upper()
    selected_index = selected_index.upper()
    
    # Common indexes and their URL patterns
    index_patterns = {
        "IEEE": ["IEEE.ORG", "COMPUTER.ORG"],
        "ACM": ["ACM.ORG", "SIGCHI", "SIGPLAN", "SIGSOFT"],
        "SCOPUS": ["SCOPUS", "ELSEVIER.COM"],
        "WEB OF SCIENCE": ["WEBOFSCIENCE", "CLARIVATE"],
        "PUBMED": ["PUBMED", "NCBI.NLM.NIH.GOV"],
        "MEDLINE": ["MEDLINE", "NLM.NIH.GOV"]
    }
    
    # Check if URL contains patterns for the selected index
    found_indexes = []
    
    for index, patterns in index_patterns.items():
        for pattern in patterns:
            if pattern in url:
                found_indexes.append(index)
                break
    
    # Check if selected index is found in URL
    url_index_match = selected_index in found_indexes
    
    return url_index_match, found_indexes

@lru_cache(maxsize=32)
def get_conference_recommendations(research_paper_text, field_of_study=None):
    """Get conference recommendations based on research paper content"""
    try:
        # Check if OpenAI client is available
        if not openai_client:
            return {
                "success": False,
                "error": "OpenAI service is not available",
                "recommendations": []
            }
            
        # Create prompt
        prompt = f"""
        Based on this research paper abstract, recommend appropriate academic conferences:
        
        Abstract:
        {research_paper_text[:2000]}
        
        Field of study: {field_of_study or "Not specified"}
        
        Recommend 5 suitable conferences where this research could be presented.
        For each conference provide:
        1. Full conference name
        2. Academic index (IEEE, ACM, Scopus, etc.)
        3. Conference tier/quality (top-tier, mid-tier, etc.)
        4. Subject alignment (how well the paper matches)
        5. Brief justification
        
        Format as JSON array with these fields: name, index, tier, alignment, justification
        """
        
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an academic research advisor who specializes in conference recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        
        return {
            "success": True,
            "recommendations": result.get("recommendations", [])
        }
        
    except Exception as e:
        logging.error(f"Error in get_conference_recommendations: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        }

def generate_conference_summary(acceptance_text, conference_name):
    """Generate a summary of conference details based on acceptance letter"""
    try:
        if not openai_client:
            return "Unable to generate summary. AI service not available."
            
        prompt = f"""
        Based on this conference acceptance letter, extract and summarize the key information:
        
        Acceptance letter:
        {acceptance_text[:2000]}
        
        Conference name: {conference_name}
        
        Create a concise summary (max 100 words) highlighting:
        - Main conference focus
        - Key dates
        - Location details
        - Any special requirements
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes conference information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logging.error(f"Error generating conference summary: {str(e)}")
        return f"Unable to generate summary: {str(e)}"

def generate_ai_notes(conference_name, purpose, index_type, destination_country, city):
    """Generate helpful notes about conference and destination"""
    try:
        if not openai_client:
            return "Unable to generate notes. AI service not available."
            
        prompt = f"""
        Generate helpful travel notes for a professor attending this academic conference:
        
        Conference: {conference_name}
        Purpose: {purpose}
        Academic index: {index_type}
        Destination: {city}, {destination_country}
        
        Provide concise notes (max 150 words) including:
        1. Academic relevance
        2. Key travel considerations for this location
        3. Cultural or professional tips
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable academic travel advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=250
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logging.error(f"Error generating AI notes: {str(e)}")
        return f"Unable to generate notes: {str(e)}"

def analyze_research_paper(paper_text):
    """Analyze research paper for strengths, weaknesses and recommendations"""
    try:
        if not openai_client:
            return {
                "success": False,
                "error": "AI service not available"
            }
            
        prompt = f"""
        Analyze this research paper excerpt and provide academic feedback:
        
        {paper_text[:3000]}
        
        Provide structured analysis with these sections:
        1. Key strengths (3 points)
        2. Areas for improvement (3 points)
        3. Publication readiness (scale 1-10)
        4. Specific recommendations
        
        Format response as JSON with these keys: strengths, improvements, readiness, recommendations
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert academic reviewer who provides constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing research paper: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }