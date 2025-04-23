"""
Login and authentication module.
Handles user authentication and account management.
"""

import hashlib
import logging
import streamlit as st
from datetime import datetime, timedelta
import uuid

from app.database.connection import DatabaseManager
from app.utils.security import get_client_ip
from app.config import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES

def check_credentials(user_id, password):
    """Check user credentials against the database"""
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    result = DatabaseManager.execute_query(
        "SELECT * FROM faculty WHERE user_id = %s AND password = %s",
        (user_id, hashed_password)
    )
    
    if result:
        st.session_state.user_role = result[0]["role"]
        st.session_state.user_name = result[0]["name"]
        return True
    return False

def secure_login(user_id, password):
    """Enhanced secure login with rate limiting and logging"""
    # Check for account lockout
    if st.session_state.get("lockout_until"):
        if datetime.now() < st.session_state.lockout_until:
            remaining = st.session_state.lockout_until - datetime.now()
            st.error(
                f"Account temporarily locked. Try again in {remaining.seconds//60} minutes."
            )
            return False

    # Basic input validation
    if not user_id or not password:
        st.error("Please provide both ID and password.")
        return False

    # Check credentials
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        result = DatabaseManager.execute_query(
            "SELECT * FROM faculty WHERE user_id = %s AND password = %s",
            (user_id, hashed_password),
        )

        if result and len(result) > 0:
            # Reset login attempts on successful login
            st.session_state.login_attempts = 0

            # Set user session data
            st.session_state.logged_in_user = user_id
            st.session_state.user_role = result[0]["role"]
            st.session_state.user_name = result[0]["name"]
            st.session_state.page = "main"
            st.session_state.last_activity = datetime.now()

            # Log successful login
            ip_address = get_client_ip()
            logging.info(f"Login successful: {user_id} from IP {ip_address}")

            # Record login in activity log
            record_user_activity(
                user_id,
                "login",
                {"ip_address": ip_address, "session_id": st.session_state.session_id},
            )

            return True
        else:
            # Increment failed login attempts
            st.session_state.login_attempts += 1

            # Log failed login attempt
            ip_address = get_client_ip()
            logging.warning(
                f"Failed login attempt: {user_id} from IP {ip_address}. Attempt #{st.session_state.login_attempts}"
            )

            # Implement account lockout after multiple failed attempts
            if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                lockout_time = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                st.session_state.lockout_until = lockout_time
                logging.warning(
                    f"Account {user_id} locked until {lockout_time} due to multiple failed login attempts."
                )
                st.error(
                    f"Too many failed login attempts. Your account has been temporarily locked for {LOCKOUT_DURATION_MINUTES} minutes."
                )
            else:
                st.error("Invalid ID or password.")

            return False

    except Exception as e:
        logging.error(f"Error during login: {str(e)}")
        st.error("An error occurred during login. Please try again.")
        return False

def login_callback():
    """Handle user login"""
    user_id = st.session_state.get("user_id_input")
    password = st.session_state.get("password_input")

    if user_id and password and check_credentials(user_id, password):
        # Clear previous session data
        for key in list(st.session_state.keys()):
            if key not in ["page", "logged_in_user", "user_role", "user_name"]:
                del st.session_state[key]

        # Set new session data
        st.session_state.logged_in_user = user_id
        st.session_state.page = "main"
        st.session_state.submitted = False
        st.session_state.login_attempted = True
        st.session_state.show_success = True

    else:
        st.error("Invalid ID or password.")
        st.session_state.login_attempted = False

def logout():
    """Enhanced secure logout with activity logging"""
    if st.session_state.logged_in_user:
        # Log the logout action
        user_id = st.session_state.logged_in_user
        logging.info(f"User {user_id} logged out")

        # Record logout in activity log
        record_user_activity(
            user_id, "logout", {"session_id": st.session_state.session_id}
        )

    # Clear all session state
    for key in list(st.session_state.keys()):
        if key != "session_id":  # Keep session ID for tracking
            del st.session_state[key]

    # Reset basic session variables
    st.session_state.page = "login"
    st.session_state.logged_in_user = None
    st.session_state.user_role = None
    st.session_state.last_activity = datetime.now()
    st.session_state.login_attempts = 0
    st.session_state.logout_requested = True

def record_user_activity(user_id, activity_type, details=None):
    """Record user activity for audit purposes"""
    import json
    try:
        details_json = json.dumps(details) if details else "{}"

        DatabaseManager.execute_query(
            """
            INSERT INTO user_activity_log 
            (user_id, activity_type, details, ip_address, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (user_id, activity_type, details_json, get_client_ip()),
            fetch=False,
            commit=True,
        )
    except Exception as e:
        logging.error(f"Error recording user activity: {str(e)}")