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
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
        }
        if self.details:
            result["details"] = self.details
        return result
    
    @staticmethod
    def from_exception(exc):
        """Convert a standard exception to an AppError."""
        # Create appropriate AppError based on exception type
        if isinstance(exc, ValueError):
            return ValidationError(str(exc))
        elif isinstance(exc, LookupError):
            return NotFoundError(str(exc))
        elif isinstance(exc, PermissionError):
            return AuthorizationError(str(exc))
        else:
            # Generic error for other exception types
            details = {
                "exception_type": exc.__class__.__name__,
                "traceback": traceback.format_exc()
            }
            return AppError(str(exc), details=details)

class ValidationError(AppError):
    """Error for validation failures."""
    
    def __init__(self, message, field=None, details=None):
        """
        Initialize the validation error.
        
        Args:
            message: Error message
            field: Optional field name
            details: Optional error details
        """
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR", details=details)
    
    def to_dict(self):
        """Convert validation error to dictionary representation."""
        result = super().to_dict()
        if self.field:
            result["field"] = self.field
        return result

class DatabaseError(AppError):
    """Error for database operations."""
    
    def __init__(self, message, query=None, details=None):
        """
        Initialize the database error.
        
        Args:
            message: Error message
            query: Optional query string
            details: Optional error details
        """
        self.query = query
        super().__init__(message, code="DATABASE_ERROR", details=details)
    
    def to_dict(self):
        """Convert database error to dictionary representation."""
        result = super().to_dict()
        # Don't include the actual query in the response for security
        # but log it for debugging
        if self.query:
            logging.debug(f"Database error query: {self.query}")
        return result

class AuthenticationError(AppError):
    """Error for authentication failures."""
    
    def __init__(self, message, details=None):
        """
        Initialize the authentication error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="AUTHENTICATION_ERROR", details=details)

class AuthorizationError(AppError):
    """Error for authorization failures."""
    
    def __init__(self, message, required_role=None, details=None):
        """
        Initialize the authorization error.
        
        Args:
            message: Error message
            required_role: Optional required role
            details: Optional error details
        """
        self.required_role = required_role
        super().__init__(message, code="AUTHORIZATION_ERROR", details=details)
    
    def to_dict(self):
        """Convert authorization error to dictionary representation."""
        result = super().to_dict()
        if self.required_role:
            result["required_role"] = self.required_role
        return result

class ServiceError(AppError):
    """Error for service failures."""
    
    def __init__(self, message, service=None, details=None):
        """
        Initialize the service error.
        
        Args:
            message: Error message
            service: Optional service name
            details: Optional error details
        """
        self.service = service
        super().__init__(message, code="SERVICE_ERROR", details=details)
    
    def to_dict(self):
        """Convert service error to dictionary representation."""
        result = super().to_dict()
        if self.service:
            result["service"] = self.service
        return result

class NotFoundError(AppError):
    """Error for resource not found."""
    
    def __init__(self, message, resource_type=None, resource_id=None, details=None):
        """
        Initialize the not found error.
        
        Args:
            message: Error message
            resource_type: Optional resource type
            resource_id: Optional resource ID
            details: Optional error details
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, code="NOT_FOUND_ERROR", details=details)
    
    def to_dict(self):
        """Convert not found error to dictionary representation."""
        result = super().to_dict()
        if self.resource_type:
            result["resource_type"] = self.resource_type
        if self.resource_id:
            result["resource_id"] = self.resource_id
        return result

class ConfigurationError(AppError):
    """Error for configuration issues."""
    
    def __init__(self, message, setting=None, details=None):
        """
        Initialize the configuration error.
        
        Args:
            message: Error message
            setting: Optional setting name
            details: Optional error details
        """
        self.setting = setting
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)
    
    def to_dict(self):
        """Convert configuration error to dictionary representation."""
        result = super().to_dict()
        if self.setting:
            result["setting"] = self.setting
        return result

def handle_errors(func):
    """
    Decorator to handle errors in service functions.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Log the error
            logging.error(f"{e.__class__.__name__}: {e.message}")
            
            # Capture the error for monitoring
            capture_error(e)
            
            # Return error response
            return {
                "success": False,
                "error": e.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Convert to AppError and handle
            app_error = AppError.from_exception(e)
            
            # Log the error
            logging.error(f"Uncaught exception in {func.__name__}: {str(e)}")
            logging.error(traceback.format_exc())
            
            # Capture the error for monitoring
            capture_error(e)
            
            # Return error response
            return {
                "success": False,
                "error": app_error.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
    
    return wrapper

def handle_ui_errors(func):
    """
    Decorator to handle errors in UI functions.
    Displays error messages in the UI instead of returning them.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with UI error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Log the error
            logging.error(f"{e.__class__.__name__}: {e.message}")
            
            # Capture the error for monitoring
            capture_error(e)
            
            # Display error in UI
            display_error(e)
            
            # Return None to indicate error
            return None
        except Exception as e:
            # Convert to AppError and handle
            app_error = AppError.from_exception(e)
            
            # Log the error
            logging.error(f"Uncaught exception in {func.__name__}: {str(e)}")
            logging.error(traceback.format_exc())
            
            # Capture the error for monitoring
            capture_error(e)
            
            # Display error in UI
            display_error(app_error)
            
            # Return None to indicate error
            return None
    
    return wrapper

def validate_input(validation_func):
    """
    Decorator to validate function inputs.
    
    Args:
        validation_func: Function that validates inputs and returns (is_valid, error_message)
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Run validation
            is_valid, message = validation_func(*args, **kwargs)
            
            if not is_valid:
                raise ValidationError(message)
            
            # Proceed with function if validation passes
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def display_error(error):
    """
    Display an error in the Streamlit UI.
    
    Args:
        error: Error object to display
    """
    if isinstance(error, AppError):
        error_type = error.__class__.__name__
        message = error.message
    else:
        error_type = error.__class__.__name__
        message = str(error)
    
    error_html = f"""
    <div style="background-color: #FEE2E2; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
        <h3 style="color: #B91C1C; margin-top: 0;">{error_type}</h3>
        <p style="margin-bottom: 0.5rem;">{message}</p>
    """
    
    # Add details if available
    if isinstance(error, AppError) and error.details:
        details_str = json.dumps(error.details, indent=2)
        error_html += f"""
        <details>
            <summary style="cursor: pointer; margin-top: 0.5rem;">Error Details</summary>
            <pre style="background-color: #FECACA; padding: 0.5rem; border-radius: 0.25rem; 
                 margin-top: 0.5rem; white-space: pre-wrap;">{details_str}</pre>
        </details>
        """
    
    error_html += "</div>"
    
    st.markdown(error_html, unsafe_allow_html=True)

class ErrorContext:
    """Context manager for error handling."""
    
    def __init__(self, context_name=None, error_message=None):
        """
        Initialize the error context.
        
        Args:
            context_name: Optional name for the context
            error_message: Optional error message override
        """
        self.context_name = context_name
        self.error_message = error_message
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle the exception
            if isinstance(exc_val, AppError):
                # Add context information to existing AppError
                if self.context_name:
                    if exc_val.details is None:
                        exc_val.details = {}
                    exc_val.details["context"] = self.context_name
                
                # Use custom error message if provided
                if self.error_message:
                    exc_val.message = self.error_message
                
                # Log the error
                logging.error(f"{exc_val.__class__.__name__} in {self.context_name}: {exc_val.message}")
                
                # Capture the error for monitoring
                capture_error(exc_val)
                
                # Display in UI if in Streamlit context
                if st._is_running:
                    display_error(exc_val)
                
                return True  # Exception handled
            else:
                # Convert to AppError and handle
                app_error = AppError.from_exception(exc_val)
                
                # Add context information
                if self.context_name:
                    if app_error.details is None:
                        app_error.details = {}
                    app_error.details["context"] = self.context_name
                
                # Use custom error message if provided
                if self.error_message:
                    app_error.message = self.error_message
                
                # Log the error
                logging.error(f"Exception in {self.context_name}: {str(exc_val)}")
                logging.error(traceback.format_exc())
                
                # Capture the error for monitoring
                capture_error(exc_val)
                
                # Display in UI if in Streamlit context
                if st._is_running:
                    display_error(app_error)
                
                # Re-raise as AppError
                raise app_error
        
        return False  # No exception occurred

def form_validator(form_data, validation_rules):
    """
    Validate form data against rules.
    
    Args:
        form_data: Dictionary of form data
        validation_rules: Dictionary of field name to validation function
        
    Returns:
        (is_valid, errors): Tuple of validation status and error messages
    """
    errors = {}
    
    for field, validator in validation_rules.items():
        # Skip fields not in the form data
        if field not in form_data:
            continue
        
        # Get field value
        value = form_data[field]
        
        # Validate field
        is_valid, message = validator(value)
        
        if not is_valid:
            errors[field] = message
    
    return len(errors) == 0, errors