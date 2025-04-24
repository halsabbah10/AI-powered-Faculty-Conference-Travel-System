"""
Faculty Conference Travel System - Main Application
Entry point for the Streamlit application
"""

import streamlit as st
import os
import logging
from datetime import datetime
import uuid

# Import modules from our application
from app.config import load_environment
from app.utils.security import setup_logging, hash_password
from app.auth.session import setup_session_state, check_session_security
from app.ui.common import load_css, display_header, display_footer, display_user_info
from app.ui.common import display_success_box, display_error_box
from app.auth.csrf import add_csrf_protection, check_csrf_token
from app.auth.rate_limit import login_rate_limiter

# Import role-specific UI modules
from app.ui.professor import show_professor_dashboard
from app.ui.accountant import show_accountant_dashboard  
from app.ui.approval import show_approval_dashboard

# Import database functionality
from app.database.queries import get_user_by_id, log_user_activity

# Set up logging
setup_logging()

# Load environment variables
load_environment()

# Set up page configuration
st.set_page_config(
    page_title="Faculty Conference Travel System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# Initialize session state
setup_session_state()

# Check session security (timeout, etc.)
def check_session():
    if "logged_in_user" not in st.session_state:
        return False
    if not st.session_state.logged_in_user:
        return False
    return check_session_security()

def show_admin_panel():
    """Display admin panel with system management tools."""
    from app.ui.admin import show_admin_dashboard
    from app.utils.feature_flags import show_feature_flags_manager
    from app.utils.accessibility import show_accessibility_dashboard
    from app.utils.performance import show_performance_dashboard
    from app.ui.configuration import show_configuration_panel
    
    st.sidebar.title("Admin Tools")
    admin_page = st.sidebar.radio(
        "Select Tool",
        ["System Dashboard", "Feature Flags", "Performance", "Accessibility", "Configuration"]
    )
    
    if admin_page == "System Dashboard":
        show_admin_dashboard()
    elif admin_page == "Feature Flags":
        show_feature_flags_manager()
    elif admin_page == "Performance":
        show_performance_dashboard()
    elif admin_page == "Accessibility":
        show_accessibility_dashboard()
    elif admin_page == "Configuration":
        show_configuration_panel()

def main():
    """Main application entry point"""
    # Initialize error monitoring
    from app.utils.error_monitoring import init_error_monitoring
    init_error_monitoring()
    
    # Add accessibility features
    from app.utils.accessibility import add_accessibility_features
    add_accessibility_features()
    
    # Display user info in sidebar if logged in
    if "logged_in_user" in st.session_state and st.session_state.logged_in_user:
        display_user_info()
    
    # Check if user is logged in
    if not check_session():
        show_login_page()
        return
    
    # Route to appropriate dashboard based on role
    if st.session_state.user_role == "professor":
        show_professor_dashboard()
    elif st.session_state.user_role == "accountant":
        show_accountant_dashboard()
    elif st.session_state.user_role == "approval":
        show_approval_dashboard()
    elif st.session_state.user_role == "admin":
        show_admin_panel()
    else:
        st.error("Unknown user role. Please contact system administrator.")
    
    # Display footer
    display_footer()

def show_login_page():
    """Display login page with enhanced security"""
    display_header("Faculty Conference Travel System", show_logout=False)
    
    # Get client IP for rate limiting
    client_ip = st.session_state.get("client_ip", "unknown")
    
    # Check if user is rate limited
    is_blocked, wait_time = login_rate_limiter.is_blocked(client_ip)
    if is_blocked:
        display_error_box(
            f"Too many failed login attempts. Please try again in {wait_time} seconds."
        )
        return
    
    st.markdown("""
    <div class='info-box'>
        Welcome to the Faculty Conference Travel System. Please log in to continue.
    </div>
    """, unsafe_allow_html=True)
    
    # Generate CSRF token
    csrf_token = add_csrf_protection("login_csrf_token")
    
    with st.form("login_form"):
        user_id = st.text_input("User ID", key="user_id_input")
        password = st.text_input("Password", type="password", key="password_input")
        
        # Hidden field for CSRF token
        submitted_token = st.text_input("", value=csrf_token, key="csrf_token_input", type="password", label_visibility="collapsed")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Verify CSRF token
            if not check_csrf_token(submitted_token, "login_csrf_token"):
                display_error_box("Invalid form submission. Please try again.")
                return
                
            process_login(user_id, password)

def process_login(user_id, password):
    """Process login attempt with rate limiting"""
    client_ip = st.session_state.get("client_ip", "unknown")
    
    if not user_id or not password:
        # Record failed attempt
        login_rate_limiter.record_attempt(client_ip, success=False)
        display_error_box("Please enter both User ID and Password")
        return
    
    # Hash password for security
    hashed_password = hash_password(password)
    
    # Check credentials
    user = get_user_by_id(user_id)
    
    if user and user['password'] == hashed_password:
        # Record successful attempt
        login_rate_limiter.record_attempt(client_ip, success=True)
        
        # Set session state
        st.session_state.logged_in_user = user_id
        st.session_state.user_name = user['name']
        st.session_state.user_role = user['role']
        st.session_state.login_time = datetime.now()
        
        # Log activity
        log_user_activity(
            user_id, 
            "login", 
            {"success": True}, 
            client_ip
        )
        
        display_success_box(f"Welcome, {user['name']}!")
        st.experimental_rerun()
    else:
        # Record failed attempt
        is_blocked, attempts_left = login_rate_limiter.record_attempt(client_ip, success=False)
        
        # Log failed attempt
        log_user_activity(
            user_id or "unknown", 
            "login", 
            {"success": False}, 
            client_ip
        )
        
        if is_blocked:
            display_error_box("Too many failed login attempts. Your account has been temporarily locked.")
        else:
            display_error_box(f"Invalid credentials. Please try again. ({attempts_left} attempts remaining)")

if __name__ == "__main__":
    main()