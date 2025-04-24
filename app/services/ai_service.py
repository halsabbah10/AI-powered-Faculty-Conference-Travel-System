"""
AI services module.
Provides AI-powered analysis and features.
"""

import os
import time
import logging
import openai
import google.generativeai as genai
from datetime import datetime
import functools
from app.utils.performance import timer
from app.utils.feature_flags import FeatureFlags
from app.utils.error_monitoring import capture_error

# Configure API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))

def cache_expensive_operation(func):
    """Cache results of expensive AI operations."""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a cache key from the function name and arguments
        key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
        
        # Check if result is in cache and not expired (24 hours)
        if key in cache:
            timestamp, result = cache[key]
            if datetime.now().timestamp() - timestamp < 86400:  # 24 hours
                logging.info(f"Cache hit for {func.__name__}")
                return result
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        cache[key] = (datetime.now().timestamp(), result)
        
        # Limit cache size
        if len(cache) > 100:
            # Remove oldest entries
            sorted_keys = sorted(cache.keys(), key=lambda k: cache[k][0])
            for old_key in sorted_keys[:10]:
                del cache[old_key]
                
        return result
    
    return wrapper

@capture_error
@timer(label="AI-Conference-Validation")
@cache_expensive_operation
def validate_conference(conference_name, conference_url, destination=None):
    """
    Validate conference legitimacy using AI.
    
    Args:
        conference_name: Name of the conference
        conference_url: URL of the conference website
        destination: Optional destination/location
        
    Returns:
        dict: Validation results
    """
    # Check if AI analysis is enabled
    if not FeatureFlags.is_enabled("ai_analysis"):
        logging.info("AI analysis is disabled, skipping conference validation")
        return {
            "legitimate": True,
            "confidence": 0.5,
            "notes": "AI analysis is currently disabled. Manual verification recommended.",
            "potential_issues": []
        }
    
    try:
        # Prepare prompt
        prompt = f"""
        Analyze the following academic conference for legitimacy:
        
        Conference Name: {conference_name}
        Conference Website: {conference_url}
        Destination: {destination or 'Not provided'}
        
        Please determine if this appears to be a legitimate academic conference or potentially a predatory/fake conference.
        Consider factors such as:
        1. Is this a known and established conference?
        2. Does the website look professional and provide clear information?
        3. Is the conference location consistent with the conference topic?
        4. Are there any red flags that suggest this might be a predatory conference?
        
        Provide your assessment with:
        - Legitimacy determination (legitimate or potentially predatory)
        - Confidence level (0.0 to 1.0)
        - Specific notes and observations
        - List of potential issues if any
        """
        
        # Choose AI provider based on configuration
        ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        
        if ai_provider == "google":
            return _analyze_with_google_ai(prompt)
        else:
            return _analyze_with_openai(prompt)
            
    except Exception as e:
        logging.error(f"Error validating conference: {str(e)}")
        # Return safe fallback
        return {
            "legitimate": True,
            "confidence": 0.0,
            "notes": f"Error during AI analysis: {str(e)}. Manual verification required.",
            "potential_issues": ["AI analysis failed"]
        }

@capture_error
@timer(label="AI-Paper-Analysis")
@cache_expensive_operation
def analyze_research_paper(paper_text, conference_name=None):
    """
    Analyze research paper content using AI.
    
    Args:
        paper_text: Text content of the paper
        conference_name: Optional name of the target conference
        
    Returns:
        dict: Analysis results
    """
    # Check if AI analysis is enabled
    if not FeatureFlags.is_enabled("ai_analysis"):
        logging.info("AI analysis is disabled, skipping paper analysis")
        return {
            "quality_score": 0.5,
            "summary": "AI analysis is currently disabled. Manual review recommended.",
            "strengths": ["Could not be automatically analyzed"],
            "weaknesses": ["Could not be automatically analyzed"],
            "suggestions": ["Enable AI analysis for detailed feedback"]
        }
    
    try:
        # Limit text length to avoid token limits
        max_length = 8000
        if len(paper_text) > max_length:
            paper_text = paper_text[:max_length] + "... [truncated]"
        
        # Prepare prompt
        prompt = f"""
        Analyze the following research paper{' for ' + conference_name if conference_name else ''}:
        
        {paper_text}
        
        Please provide an academic assessment of this paper with:
        1. A quality score from 0.0 to 1.0
        2. A brief summary of the paper (3-5 sentences)
        3. Key strengths (3-5 points)
        4. Potential weaknesses or areas for improvement (3-5 points)
        5. Specific suggestions to improve the paper (3-5 points)
        """
        
        # Choose AI provider based on configuration
        ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        
        if ai_provider == "google":
            return _process_paper_analysis(_analyze_with_google_ai(prompt))
        else:
            return _process_paper_analysis(_analyze_with_openai(prompt))
            
    except Exception as e:
        logging.error(f"Error analyzing research paper: {str(e)}")
        # Return safe fallback
        return {
            "quality_score": 0.5,
            "summary": f"Error during analysis: {str(e)}. Manual review required.",
            "strengths": ["Could not be automatically analyzed"],
            "weaknesses": ["Could not be automatically analyzed"],
            "suggestions": ["Try again later or request manual review"]
        }

@capture_error
@timer(label="AI-Notes-Generation")
def generate_ai_notes(request_data, user_data=None, paper_text=None):
    """
    Generate AI-powered notes for a request.
    
    Args:
        request_data: Request information
        user_data: Optional user information
        paper_text: Optional paper text
        
    Returns:
        str: Generated notes
    """
    # Check if AI analysis is enabled
    if not FeatureFlags.is_enabled("ai_analysis"):
        logging.info("AI analysis is disabled, skipping notes generation")
        return "AI analysis is currently disabled. Please review the request manually."
    
    try:
        # Construct context
        context = f"""
        Faculty: {user_data['name'] if user_data else request_data.get('faculty_name', 'Unknown')}
        Department: {user_data['department'] if user_data else request_data.get('department', 'Unknown')}
        Conference: {request_data.get('conference_name', 'Unknown')}
        Destination: {request_data.get('destination', 'Unknown')}, {request_data.get('city', 'Unknown')}
        Dates: {request_data.get('date_from', 'Unknown')} to {request_data.get('date_to', 'Unknown')}
        Purpose: {request_data.get('purpose_of_attending', 'Unknown')}
        
        Budget Details:
        - Registration: ${request_data.get('registration_fee', 0)}
        - Per Diem: ${request_data.get('per_diem', 0)}
        - Visa Fee: ${request_data.get('visa_fee', 0)}
        """
        
        if paper_text:
            # Add truncated paper summary
            max_paper_length = 3000
            paper_summary = paper_text[:max_paper_length] + "..." if len(paper_text) > max_paper_length else paper_text
            context += f"\n\nPaper Abstract: {paper_summary}"
        
        # Prepare prompt
        prompt = f"""
        Based on the following conference travel request:
        
        {context}
        
        Please provide helpful notes for the approver, including:
        1. Assessment of the conference's relevance to the faculty's field
        2. Assessment of the budget reasonableness
        3. Any potential concerns or special considerations
        4. Recommendation for approval or further review
        
        Keep your response concise and professional.
        """
        
        # Choose AI provider based on configuration
        ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        
        if ai_provider == "google":
            response = _analyze_with_google_ai(prompt)
            return response.get("text", "Error generating notes. Please review manually.")
        else:
            response = _analyze_with_openai(prompt)
            return response.get("text", "Error generating notes. Please review manually.")
            
    except Exception as e:
        logging.error(f"Error generating AI notes: {str(e)}")
        return f"Error generating AI notes: {str(e)}. Please review the request manually."

def _analyze_with_openai(prompt):
    """Use OpenAI API for analysis."""
    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "You are a helpful academic assistant analyzing conference travel requests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        output = response.choices[0].message.content.strip()
        
        # Parse output into structured format
        import re
        
        # For conference validation
        if "legitimacy determination" in prompt.lower():
            legitimate = "legitimate" in output.lower() and "not legitimate" not in output.lower()
            
            # Extract confidence
            confidence_match = re.search(r'confidence level:?\s*(0\.\d+|1\.0)', output, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            # Extract issues
            issues = []
            issues_section = re.search(r'potential issues:?\s*(.*?)(?:\n\n|$)', output, re.IGNORECASE | re.DOTALL)
            if issues_section:
                issue_text = issues_section.group(1)
                # Look for list items
                list_items = re.findall(r'(?:^|\n)(?:- |\d+\. )(.*?)(?:\n|$)', issue_text)
                if list_items:
                    issues = [item.strip() for item in list_items if item.strip()]
                else:
                    # No list format, use the whole section
                    issues = [issue_text.strip()]
            
            return {
                "legitimate": legitimate,
                "confidence": confidence,
                "notes": output,
                "potential_issues": issues
            }
            
        # For paper analysis and general notes
        return {
            "text": output
        }
        
    except Exception as e:
        logging.error(f"Error with OpenAI API: {str(e)}")
        raise

def _analyze_with_google_ai(prompt):
    """Use Google Generative AI for analysis."""
    try:
        model = genai.GenerativeModel(os.getenv("GOOGLE_AI_MODEL", "gemini-pro"))
        response = model.generate_content(prompt)
        
        output = response.text.strip()
        
        # Parse output similar to OpenAI function
        import re
        
        # For conference validation
        if "legitimacy determination" in prompt.lower():
            legitimate = "legitimate" in output.lower() and "not legitimate" not in output.lower()
            
            # Extract confidence
            confidence_match = re.search(r'confidence level:?\s*(0\.\d+|1\.0)', output, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            # Extract issues
            issues = []
            issues_section = re.search(r'potential issues:?\s*(.*?)(?:\n\n|$)', output, re.IGNORECASE | re.DOTALL)
            if issues_section:
                issue_text = issues_section.group(1)
                # Look for list items
                list_items = re.findall(r'(?:^|\n)(?:- |\d+\. )(.*?)(?:\n|$)', issue_text)
                if list_items:
                    issues = [item.strip() for item in list_items if item.strip()]
                else:
                    # No list format, use the whole section
                    issues = [issue_text.strip()]
            
            return {
                "legitimate": legitimate,
                "confidence": confidence,
                "notes": output,
                "potential_issues": issues
            }
            
        # For paper analysis and general notes
        return {
            "text": output
        }
        
    except Exception as e:
        logging.error(f"Error with Google AI API: {str(e)}")
        raise

def _process_paper_analysis(response):
    """Process and structure the paper analysis response."""
    try:
        text = response.get("text", "")
        import re
        
        # Extract quality score
        score_match = re.search(r'quality score:?\s*(0\.\d+|1\.0)', text, re.IGNORECASE)
        quality_score = float(score_match.group(1)) if score_match else 0.5
        
        # Extract summary
        summary_match = re.search(r'summary:?\s*(.*?)(?:\n\n|\n(?=\d+\.)|\n(?=Key strengths))', text, re.IGNORECASE | re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "No summary provided."
        
        # Extract strengths
        strengths = []
        strengths_section = re.search(r'(?:key )?strengths:?\s*(.*?)(?:\n\n|\n(?=\d+\.)|\n(?=Potential weaknesses))', text, re.IGNORECASE | re.DOTALL)
        if strengths_section:
            strength_text = strengths_section.group(1)
            # Look for list items
            list_items = re.findall(r'(?:^|\n)(?:- |\d+\. )(.*?)(?:\n|$)', strength_text)
            if list_items:
                strengths = [item.strip() for item in list_items if item.strip()]
            
        # Extract weaknesses
        weaknesses = []
        weaknesses_section = re.search(r'(?:potential )?weaknesses:?\s*(.*?)(?:\n\n|\n(?=\d+\.)|\n(?=Specific suggestions))', text, re.IGNORECASE | re.DOTALL)
        if weaknesses_section:
            weakness_text = weaknesses_section.group(1)
            # Look for list items
            list_items = re.findall(r'(?:^|\n)(?:- |\d+\. )(.*?)(?:\n|$)', weakness_text)
            if list_items:
                weaknesses = [item.strip() for item in list_items if item.strip()]
        
        # Extract suggestions
        suggestions = []
        suggestions_section = re.search(r'(?:specific )?suggestions:?\s*(.*?)(?:\n\n|$)', text, re.IGNORECASE | re.DOTALL)
        if suggestions_section:
            suggestion_text = suggestions_section.group(1)
            # Look for list items
            list_items = re.findall(r'(?:^|\n)(?:- |\d+\. )(.*?)(?:\n|$)', suggestion_text)
            if list_items:
                suggestions = [item.strip() for item in list_items if item.strip()]
        
        # Ensure all lists have at least one item
        if not strengths:
            strengths = ["No specific strengths identified."]
        if not weaknesses:
            weaknesses = ["No specific weaknesses identified."]
        if not suggestions:
            suggestions = ["No specific suggestions provided."]
        
        return {
            "quality_score": quality_score,
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logging.error(f"Error processing paper analysis: {str(e)}")
        return {
            "quality_score": 0.5,
            "summary": "Error processing analysis.",
            "strengths": ["Processing error"],
            "weaknesses": ["Processing error"],
            "suggestions": ["Please review manually"]
        }