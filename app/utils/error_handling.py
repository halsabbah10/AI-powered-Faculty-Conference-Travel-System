"""
Error handling module.
Provides standardized error handling for the application.
"""

import logging
import traceback
import functools
import json
from datetime import datetime
import streamlit as st
from app.utils.error_monitoring import capture_error

class AppError(Exception):
    """Base class for application errors."""
    
    def __init__(self, message, code=None, details=None):
        """
        Initialize the error.
        
        Args:
            message: Error message
            code: Optional error code
            details: Optional error details
        """
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)
    
    def to_dict(self):
        """Convert error to dictionary representation."""
        result = {
            "error": True,
            "message": self.message,
        }
        
        if self.code:
            result["code"] = self.code
            
        if self.details:
            result["details"] = self.details
            
        return result
    
    def log(self):
        """Log the error with appropriate context."""
        error_data = self.to_dict()
        logging.error(f"{self.__class__.__name__}: {json.dumps(error_data)}")


class ValidationError(AppError):
    """Error raised during data validation."""
    
    def __init__(self, message, field=None, details=None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Optional field name that failed validation
            details: Optional validation details
        """
        code = "VALIDATION_ERROR"
        
        # Build field-specific details
        if field and not details:
            details = {field: message}
        elif field and isinstance(details, dict):
            details = {**details, field: message}
        
        super().__init__(message, code, details)
        self.field = field


class DatabaseError(AppError):
    """Error raised during database operations."""
    
    def __init__(self, message, query=None, params=None, details=None):
        """
        Initialize database error.
        
        Args:
            message: Error message
            query: Optional SQL query that caused the error
            params: Optional query parameters
            details: Optional error details
        """
        code = "DATABASE_ERROR"
        
        # Remove sensitive data from query if present
        if query:
            # Sanitize query to remove potential passwords, tokens, etc.
            query = self._sanitize_query(query)
        
        # Build error details
        error_details = details or {}
        if query:
            error_details["query"] = query
        
        super().__init__(message, code, error_details)
    
    def _sanitize_query(self, query):
        """Remove sensitive information from SQL query."""
        # Replace password patterns
        return query.replace("password = %s", "password = [REDACTED]")


class AuthenticationError(AppError):
    """Error raised during authentication."""
    
    def __init__(self, message, user_id=None, details=None):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            user_id: Optional user ID
            details: Optional error details
        """
        code = "AUTHENTICATION_ERROR"
        super().__init__(message, code, details)
        self.user_id = user_id


class AuthorizationError(AppError):
    """Error raised during authorization."""
    
    def __init__(self, message, resource=None, action=None, details=None):
        """
        Initialize authorization error.
        
        Args:
            message: Error message
            resource: Optional resource being accessed
            action: Optional action being performed
            details: Optional error details
        """
        code = "AUTHORIZATION_ERROR"
        
        # Build error details
        error_details = details or {}
        if resource:
            error_details["resource"] = resource
        if action:
            error_details["action"] = action
        
        super().__init__(message, code, error_details)


class ServiceError(AppError):
    """Error raised during external service calls."""
    
    def __init__(self, message, service=None, operation=None, details=None):
        """
        Initialize service error.
        
        Args:
            message: Error message
            service: Optional service name
            operation: Optional operation being performed
            details: Optional error details
        """
        code = "SERVICE_ERROR"
        
        # Build error details
        error_details = details or {}
        if service:
            error_details["service"] = service
        if operation:
            error_details["operation"] = operation
        
        super().__init__(message, code, error_details)


def handle_exceptions(show_error_to_user=True, default_message="An error occurred"):
    """
    Decorator for handling exceptions in a standardized way.
    
    Args:
        show_error_to_user: Whether to display error to user
        default_message: Default error message for non-AppErrors
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError as e:
                # Log and capture application errors
                e.log()
                capture_error(e)
                
                # Display to user if requested
                if show_error_to_user and hasattr(st, "error"):
                    st.error(e.message)
                
                # Return error dictionary
                return e.to_dict()
            except Exception as e:
                # Log and capture unexpected errors
                error_message = str(e) or default_message
                logging.error(f"Unexpected error in {func.__name__}: {error_message}")
                logging.error(traceback.format_exc())
                capture_error(e)
                
                # Display to user if requested
                if show_error_to_user and hasattr(st, "error"):
                    st.error(default_message)
                
                # Return error dictionary
                return {
                    "error": True,
                    "message": default_message,
                    "details": {"original_error": str(e)}
                }
        
        return wrapper
    
    return decorator


def validation_error_handler(func):
    """
    Decorator specifically for handling validation errors.
    Catches validation errors and displays them in a user-friendly way.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            # Log validation error
            e.log()
            
            # Display validation errors to user
            if hasattr(st, "error"):
                if e.details:
                    for field, error in e.details.items():
                        st.error(f"{field}: {error}")
                else:
                    st.error(e.message)
            
            # Return None to indicate validation failure
            return None
        except Exception as e:
            # Handle unexpected errors
            logging.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logging.error(traceback.format_exc())
            capture_error(e)
            
            # Display generic error to user
            if hasattr(st, "error"):
                st.error("An error occurred while validating your input.")
            
            # Return None to indicate validation failure
            return None
    
    return wrapper


def raise_validation_error(message, field=None, details=None):
    """
    Helper function to raise a validation error.
    
    Args:
        message: Error message
        field: Optional field name
        details: Optional error details
        
    Raises:
        ValidationError
    """
    raise ValidationError(message, field, details)