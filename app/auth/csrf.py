"""
CSRF protection module.
Provides functions for generating and validating CSRF tokens.
"""

import secrets
import hashlib
import hmac
import streamlit as st
import time
from datetime import datetime, timedelta

# Secret key for signing tokens
SECRET_KEY = st.secrets.get("CSRF_SECRET", "default-csrf-secret-key")

def generate_csrf_token(user_id=None):
    """
    Generate a CSRF token with a timestamp and user binding.
    
    Args:
        user_id: Optional user identifier to bind the token to a specific user
        
    Returns:
        str: A signed CSRF token
    """
    # Create a random token
    random_token = secrets.token_hex(16)
    
    # Add timestamp (for expiration)
    timestamp = int(time.time())
    
    # Create the base token
    base_token = f"{random_token}:{timestamp}"
    
    # Add user binding if provided
    if user_id:
        base_token = f"{base_token}:{user_id}"
    
    # Sign the token
    signature = hmac.new(
        SECRET_KEY.encode(),
        base_token.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Return the complete token
    return f"{base_token}:{signature}"

def validate_csrf_token(token, user_id=None, max_age=3600):
    """
    Validate a CSRF token.
    
    Args:
        token: The token to validate
        user_id: Optional user ID to verify user binding
        max_age: Maximum age of the token in seconds (default: 1 hour)
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        # Split the token into its components
        parts = token.split(":")
        
        # Check number of parts (with and without user binding)
        if user_id and len(parts) != 4:
            return False
        if not user_id and len(parts) != 3:
            return False
        
        # Extract components
        if user_id:
            random_token, timestamp, token_user_id, signature = parts
            # Verify user binding
            if token_user_id != user_id:
                return False
        else:
            random_token, timestamp, signature = parts
        
        # Recreate the base token for verification
        if user_id:
            base_token = f"{random_token}:{timestamp}:{user_id}"
        else:
            base_token = f"{random_token}:{timestamp}"
        
        # Verify signature
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            base_token.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return False
        
        # Check expiration
        token_time = datetime.fromtimestamp(int(timestamp))
        if datetime.now() - token_time > timedelta(seconds=max_age):
            return False
        
        return True
        
    except Exception:
        return False

def add_csrf_protection(form_key="csrf_token"):
    """
    Add CSRF protection to a Streamlit form.
    
    Args:
        form_key: Key for the hidden field in session state
        
    Returns:
        str: The generated CSRF token
    """
    # Generate token
    token = generate_csrf_token(st.session_state.get("logged_in_user"))
    
    # Store in session state
    st.session_state[form_key] = token
    
    return token

def check_csrf_token(token, form_key="csrf_token"):
    """
    Check if a submitted CSRF token is valid.
    
    Args:
        token: The token to validate
        form_key: Key for the hidden field in session state
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    # Get the stored token
    stored_token = st.session_state.get(form_key)
    
    # No stored token, fail
    if not stored_token:
        return False
    
    # Validate the submitted token
    return validate_csrf_token(
        token, 
        st.session_state.get("logged_in_user")
    )