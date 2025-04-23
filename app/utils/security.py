"""
Security utilities module.
Provides security-related functions and utilities.
"""

import hashlib
import logging
import os
import json
from datetime import datetime
import traceback

def sanitize_input(input_str, allow_html=False):
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        input_str: The string to sanitize
        allow_html: Whether to allow HTML tags (default: False)
        
    Returns:
        str: Sanitized string
    """
    if not input_str:
        return ""
        
    if isinstance(input_str, (int, float)):
        return str(input_str)
    
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Replace potentially dangerous characters
    if not allow_html:
        # Replace HTML special chars with entities
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
            "`": "&#x60;"
        }
        
        for char, replacement in replacements.items():
            input_str = input_str.replace(char, replacement)
    
    # Prevent SQL injection attempts
    sql_patterns = ["--", ";--", ";", "/*", "*/", "@@", "@", "char", "nchar", 
                    "varchar", "nvarchar", "alter", "begin", "cast", "create", 
                    "cursor", "declare", "delete", "drop", "end", "exec", 
                    "execute", "fetch", "insert", "kill", "select", "sys", 
                    "sysobjects", "syscolumns", "table", "update"]
    
    # Check for SQL patterns and escape them by adding a space
    lower_str = input_str.lower()
    for pattern in sql_patterns:
        pattern_index = lower_str.find(pattern)
        while pattern_index > -1:
            # Only consider it a SQL pattern if it's a whole word
            if (pattern_index == 0 or not lower_str[pattern_index-1].isalnum()) and \
               (pattern_index + len(pattern) == len(lower_str) or not lower_str[pattern_index+len(pattern)].isalnum()):
                # Add a space to break the pattern
                input_str = input_str[:pattern_index] + " " + input_str[pattern_index:]
                lower_str = input_str.lower()
            pattern_index = lower_str.find(pattern, pattern_index + 1)
    
    return input_str

def hash_password(password):
    """Hash a password using SHA-256 (should be replaced with bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_client_ip():
    """Get the client's IP address (placeholder)"""
    # In a production environment, this would extract the real IP
    # For Streamlit Cloud, you might use different headers
    return "127.0.0.1"  # Placeholder

def log_error(error, context=None):
    """Log error with detailed information and context"""
    tb_str = traceback.format_exception(type(error), error, error.__traceback__)
    error_details = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "traceback": "".join(tb_str),
        "context": context or {},
    }

    logging.error(
        f"Error: {error_details['error_type']}: {error_details['error_message']}"
    )
    logging.error(f"Context: {error_details['context']}")
    logging.debug(f"Traceback: {error_details['traceback']}")

    return error_details

def setup_logging(log_level=logging.INFO):
    """Set up comprehensive logging system"""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Define log file with date
    log_filename = f"logs/app_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Configure logging with both file and console output
    handlers = [
        # Rotating file handler (10MB per file, keep 10 files)
        logging.handlers.RotatingFileHandler(log_filename, maxBytes=10_485_760, backupCount=10),
        # Console handler
        logging.StreamHandler(),
    ]

    # Define detailed log format
    log_format = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure logging
    logging.basicConfig(
        level=log_level, format=log_format, datefmt=date_format, handlers=handlers
    )

    # Log startup information
    logging.info(f"Application started. Log level: {logging.getLevelName(log_level)}")

def record_audit_log(user_id, action, details):
    """Record an audit log entry."""
    log_entry = f"{datetime.now().isoformat()} - User: {user_id} - Action: {action} - Details: {details}\n"
    with open("audit.log", "a") as log_file:
        log_file.write(log_entry)
    logging.info(log_entry)