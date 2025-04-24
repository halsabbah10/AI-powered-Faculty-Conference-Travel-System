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
from app.services.interfaces import AIServiceInterface
from app.utils.error_handling import ServiceError, handle_exceptions

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

class AIService(AIServiceInterface):
    """
    AI service implementation.
    Provides AI-powered functionality for the application.
    """
    
    @handle_exceptions(default_message="Error analyzing text")
    def analyze_text(self, text, analysis_type, options=None):
        """
        Analyze text using AI.
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis (sentiment, entities, etc.)
            options: Optional analysis options
            
        Returns:
            dict: Analysis results
        """
        options = options or {}
        
        # Get AI provider based on configuration
        provider = self._get_ai_provider()
        
        # Perform analysis based on type
        if analysis_type == 'sentiment':
            return provider.analyze_sentiment(text, options)
        elif analysis_type == 'entities':
            return provider.extract_entities(text, options)
        elif analysis_type == 'summary':
            return provider.generate_summary(text, options)
        elif analysis_type == 'keywords':
            return provider.extract_keywords(text, options)
        else:
            raise ServiceError(
                f"Unsupported analysis type: {analysis_type}",
                service="AIService",
                operation="analyze_text"
            )
    
    @handle_exceptions(default_message="Error generating text")
    def generate_text(self, prompt, options=None):
        """
        Generate text using AI.
        
        Args:
            prompt: Text prompt
            options: Optional generation options
            
        Returns:
            str: Generated text
        """
        options = options or {}
        
        # Get AI provider based on configuration
        provider = self._get_ai_provider()
        
        # Generate text
        return provider.generate_text(prompt, options)
    
    @handle_exceptions(default_message="Error validating content")
    def validate_content(self, content, validation_type, options=None):
        """
        Validate content using AI.
        
        Args:
            content: Content to validate
            validation_type: Type of validation
            options: Optional validation options
            
        Returns:
            dict: Validation results
        """
        options = options or {}
        
        # Get AI provider based on configuration
        provider = self._get_ai_provider()
        
        # Perform validation based on type
        if validation_type == 'conference':
            return provider.validate_conference(content, options)
        elif validation_type == 'paper':
            return provider.validate_research_paper(content, options)
        else:
            raise ServiceError(
                f"Unsupported validation type: {validation_type}",
                service="AIService",
                operation="validate_content"
            )
    
    @handle_exceptions(default_message="Error getting recommendations")
    def get_recommendations(self, context, options=None):
        """
        Get recommendations based on context.
        
        Args:
            context: Context data for recommendations
            options: Optional recommendation options
            
        Returns:
            list: Recommendations
        """
        options = options or {}
        
        # Get AI provider based on configuration
        provider = self._get_ai_provider()
        
        # Get recommendations
        return provider.get_recommendations(context, options)
    
    def _get_ai_provider(self):
        """
        Get AI provider based on configuration.
        
        Returns:
            object: AI provider
        """
        from app.utils.feature_flags import FeatureFlags
        from app.config import get_config
        
        # Get provider from configuration
        provider_name = get_config("AI_PROVIDER", "openai")
        
        # Initialize the appropriate provider
        if provider_name.lower() == "openai":
            from app.services.ai_providers.openai_provider import OpenAIProvider
            return OpenAIProvider()
        elif provider_name.lower() == "google":
            from app.services.ai_providers.google_provider import GoogleAIProvider
            return GoogleAIProvider()
        elif provider_name.lower() == "mock":
            from app.services.ai_providers.mock_provider import MockAIProvider
            return MockAIProvider()
        else:
            raise ServiceError(
                f"Unsupported AI provider: {provider_name}",
                service="AIService",
                operation="_get_ai_provider"
            )

# Helper functions that use the AI service through service locator

def validate_with_gpt(text, validation_type):
    """
    Validate text with AI.
    
    Args:
        text: Text to validate
        validation_type: Type of validation
        
    Returns:
        dict: Validation results
    """
    from app.services.service_provider import ServiceProvider
    
    ai_service = ServiceProvider.service(AIService)
    return ai_service.validate_content(text, validation_type)

def get_conference_recommendations(research_area, keywords=None):
    """
    Get conference recommendations based on research area.
    
    Args:
        research_area: Research area
        keywords: Optional additional keywords
        
    Returns:
        list: Conference recommendations
    """
    from app.services.service_provider import ServiceProvider
    
    ai_service = ServiceProvider.service(AIService)
    
    context = {
        "research_area": research_area,
        "keywords": keywords or []
    }
    
    return ai_service.get_recommendations(context, {"type": "conference"})

def analyze_research_paper(paper_text):
    """
    Analyze research paper text.
    
    Args:
        paper_text: Research paper text
        
    Returns:
        dict: Analysis results
    """
    from app.services.service_provider import ServiceProvider
    
    ai_service = ServiceProvider.service(AIService)
    return ai_service.analyze_text(paper_text, "summary", {"type": "research_paper"})

def generate_ai_notes(request_data):
    """
    Generate AI notes for a request.
    
    Args:
        request_data: Request data
        
    Returns:
        str: Generated notes
    """
    from app.services.service_provider import ServiceProvider
    
    ai_service = ServiceProvider.service(AIService)
    
    prompt = f"""
    Generate concise notes for a travel request with the following details:
    
    Conference: {request_data.get('conference_name', 'Unknown')}
    Destination: {request_data.get('destination', 'Unknown')}, {request_data.get('city', 'Unknown')}
    Dates: {request_data.get('date_from', 'Unknown')} to {request_data.get('date_to', 'Unknown')}
    Total Cost: ${request_data.get('total_cost', 0):,.2f}
    Purpose: {request_data.get('purpose_of_attending', 'Unknown')}
    
    The notes should highlight key points for approval consideration.
    """
    
    return ai_service.generate_text(prompt)

def generate_conference_summary(conference_url):
    """
    Generate a summary of a conference from its URL.
    
    Args:
        conference_url: Conference website URL
        
    Returns:
        dict: Conference summary
    """
    from app.services.service_provider import ServiceProvider
    
    ai_service = ServiceProvider.service(AIService)
    
    # This would normally involve fetching the website content first
    # For simplicity, we'll just use the URL as context
    return ai_service.analyze_text(conference_url, "summary", {"type": "conference"})