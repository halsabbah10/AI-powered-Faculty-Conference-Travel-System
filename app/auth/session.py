"""
Session management for the Faculty Conference Travel System
Handles session state initialization and validation.
"""

import streamlit as st
from datetime import datetime, timedelta
import logging

def setup_session_state():
    """Initialize session state variables if they don't exist"""
    # User authentication
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    
    if "login_time" not in st.session_state:
        st.session_state.login_time = None
    
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now()
    
    # Page state
    if "page" not in st.session_state:
        st.session_state.page = "login" if not st.session_state.logged_in_user else "main"
    
    # Client info
    if "client_ip" not in st.session_state:
        st.session_state.client_ip = "127.0.0.1"  # Placeholder; would be set from request in production

def check_session_security():
    """Check if session has timed out or has other security issues"""
    # Update last activity time
    st.session_state.last_activity = datetime.now()
    
    # Check if user is logged in
    if not st.session_state.logged_in_user:
        return False
    
    # Check session timeout (30 minutes)
    if st.session_state.login_time:
        session_age = datetime.now() - st.session_state.login_time
        if session_age > timedelta(minutes=30):
            logging.info(f"Session timeout for user {st.session_state.logged_in_user}")
            logout_user()
            return False
    
    return True

def logout_user():
    """Log out the current user"""
    # Log activity
    if st.session_state.logged_in_user:
        from app.database.queries import log_user_activity
        log_user_activity(
            st.session_state.logged_in_user,
            "logout",
            {"reason": "user_action"},
            st.session_state.get("client_ip", "unknown")
        )
    
    # Clear session state
    st.session_state.logged_in_user = None
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.session_state.login_time = None
    st.session_state.page = "login"