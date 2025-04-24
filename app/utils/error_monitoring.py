"""
Error monitoring module.
Provides error tracking integration.
"""

import os
import sys
import traceback
import logging
import json
import uuid
import requests
from datetime import datetime
import streamlit as st

# Configuration
ERROR_TRACKING_ENABLED = os.getenv("ERROR_TRACKING_ENABLED", "False").lower() == "true"
ERROR_TRACKING_URL = os.getenv("ERROR_TRACKING_URL", "")
ERROR_TRACKING_KEY = os.getenv("ERROR_TRACKING_KEY", "")
ERROR_TRACKING_PROJECT = os.getenv("ERROR_TRACKING_PROJECT", "ftcs")

# Fallback to local error log if no service is configured
ERROR_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs",
    "error_logs.json"
)

# Ensure log directory exists
os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)

class ErrorMonitor:
    """Error monitoring and tracking service."""
    
    @staticmethod
    def capture_exception(exc=None, additional_data=None):
        """
        Capture and report an exception.
        
        Args:
            exc: Exception object (if None, will capture current exception)
            additional_data: Dictionary of additional data to include
            
        Returns:
            str: Error ID
        """
        # Generate unique error ID
        error_id = str(uuid.uuid4())
        
        # Get exception info
        if exc is not None:
            exc_type, exc_value, exc_traceback = type(exc), exc, exc.__traceback__
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # If no exception, return
        if exc_type is None:
            return None
            
        # Format traceback
        tb_frames = traceback.extract_tb(exc_traceback)
        formatted_tb = []
        
        for frame in tb_frames:
            formatted_tb.append({
                "filename": frame.filename,
                "lineno": frame.lineno,
                "name": frame.name,
                "line": frame.line
            })
        
        # Build error data
        error_data = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "type": exc_type.__name__,
            "message": str(exc_value),
            "traceback": formatted_tb,
            "additional_data": additional_data or {}
        }
        
        # Add user info if available
        if hasattr(st, "session_state") and "logged_in_user" in st.session_state:
            error_data["user"] = {
                "id": st.session_state.logged_in_user,
                "name": st.session_state.get("user_name", "Unknown"),
                "role": st.session_state.get("user_role", "Unknown")
            }
        
        # Send to error monitoring service if configured
        if ERROR_TRACKING_ENABLED and ERROR_TRACKING_URL and ERROR_TRACKING_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {ERROR_TRACKING_KEY}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "project": ERROR_TRACKING_PROJECT,
                    "error": error_data
                }
                
                requests.post(
                    ERROR_TRACKING_URL,
                    headers=headers,
                    json=data,
                    timeout=3  # Short timeout to avoid blocking
                )
                
                logging.info(f"Error reported to monitoring service: {error_id}")
                
            except Exception as e:
                logging.error(f"Failed to send error to monitoring service: {str(e)}")
                # Fall back to local logging
                ErrorMonitor._log_error_locally(error_data)
        else:
            # Log locally
            ErrorMonitor._log_error_locally(error_data)
        
        return error_id
    
    @staticmethod
    def _log_error_locally(error_data):
        """Log error to local file."""
        try:
            # Read existing logs
            if os.path.exists(ERROR_LOG_PATH):
                with open(ERROR_LOG_PATH, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            else:
                logs = []
            
            # Add new error
            logs.append(error_data)
            
            # Limit to 1000 most recent errors
            logs = logs[-1000:]
            
            # Write back
            with open(ERROR_LOG_PATH, 'w') as f:
                json.dump(logs, f, indent=2)
                
            logging.info(f"Error logged locally: {error_data['error_id']}")
            
        except Exception as e:
            logging.error(f"Failed to log error locally: {str(e)}")
    
    @staticmethod
    def get_local_errors(limit=100):
        """Get errors from local log file."""
        try:
            if os.path.exists(ERROR_LOG_PATH):
                with open(ERROR_LOG_PATH, 'r') as f:
                    logs = json.load(f)
                return logs[-limit:]
            return []
        except Exception as e:
            logging.error(f"Failed to read local error logs: {str(e)}")
            return []

def init_error_monitoring():
    """
    Initialize error monitoring.
    Sets up global exception handler.
    """
    def global_exception_handler(exctype, value, traceback):
        # Log to error monitor
        ErrorMonitor.capture_exception(value)
        
        # Call original exception handler
        sys.__excepthook__(exctype, value, traceback)
    
    # Set as global exception handler
    sys.excepthook = global_exception_handler
    
    logging.info("Error monitoring initialized")

def capture_error(func):
    """
    Decorator to capture and report errors.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Capture with function context
            ErrorMonitor.capture_exception(
                e, 
                additional_data={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
            )
            # Re-raise the exception
            raise
    
    return wrapper