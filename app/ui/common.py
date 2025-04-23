"""
Common UI components module.
Provides shared UI elements and styling.
"""

import streamlit as st
import os
import logging
from datetime import datetime
from urllib.parse import parse_qs
import re
import pandas as pd

def load_css():
    """Load custom CSS for styling the application"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1E3A8A;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #2563EB;
    }
    
    .info-box {
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    .warning-box {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    .success-box {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    .error-box {
        background-color: #FEE2E2;
        border-left: 5px solid #EF4444;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    .form-label {
        font-weight: 600;
        margin-bottom: 0.25rem;
        color: #4B5563;
    }
    
    .stButton button {
        background-color: #2563EB;
        color: white;
        font-weight: 600;
        border-radius: 0.25rem;
        padding: 0.5rem 1rem;
        border: none;
    }
    
    .stButton button:hover {
        background-color: #1D4ED8;
    }
    
    .logout-btn {
        position: absolute;
        top: 1rem;
        right: 1rem;
    }
    
    .dashboard-card {
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2563EB;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 1rem;
        color: #6B7280;
    }
    
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E5E7EB;
        color: #6B7280;
        font-size: 0.875rem;
    }
    </style>
    """, unsafe_allow_html=True)

def display_header(title, show_logout=True):
    """Display page header with optional logout button"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(f"<h1 class='main-header'>{title}</h1>", unsafe_allow_html=True)
    
    if show_logout and st.session_state.logged_in_user:
        with col3:
            if st.button("Logout", key="logout_btn", help="Log out of the system"):
                from app.auth.login import logout
                logout()
                st.experimental_rerun()

def display_info_box(message):
    """Display formatted information box"""
    st.markdown(f"<div class='info-box'>{message}</div>", unsafe_allow_html=True)

def display_success_box(message):
    """Display formatted success box"""
    st.markdown(f"<div class='success-box'>{message}</div>", unsafe_allow_html=True)

def display_warning_box(message):
    """Display formatted warning box"""
    st.markdown(f"<div class='warning-box'>{message}</div>", unsafe_allow_html=True)

def display_error_box(message):
    """Display formatted error box"""
    st.markdown(f"<div class='error-box'>{message}</div>", unsafe_allow_html=True)

def display_footer():
    """Display application footer"""
    current_year = datetime.now().year
    st.markdown(f"""
    <div class='footer'>
        © {current_year} Faculty Conference Travel System | Version 1.0.0
    </div>
    """, unsafe_allow_html=True)

def display_user_info():
    """Display current user information"""
    if st.session_state.logged_in_user:
        st.sidebar.markdown(f"""
        <div style='padding: 1rem; background-color: #F3F4F6; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <p><strong>User:</strong> {st.session_state.user_name}</p>
            <p><strong>Role:</strong> {st.session_state.user_role}</p>
        </div>
        """, unsafe_allow_html=True)

def show_loading_spinner(message="Loading..."):
    """Display a loading spinner with custom message"""
    with st.spinner(message):
        # This is a placeholder for code that would take time to run
        pass

def paginate_dataframe(df, page_size=10):
    """
    Create a pagination system for a DataFrame.
    
    Args:
        df: Pandas DataFrame to paginate
        page_size: Number of rows per page
        
    Returns:
        DataFrame slice for the current page
    """
    # Initialize pagination state if needed
    if "pagination_page" not in st.session_state:
        st.session_state.pagination_page = 0
    
    # Calculate number of pages
    n_pages = max(1, len(df) // page_size + (1 if len(df) % page_size > 0 else 0))
    
    # Ensure current page is valid
    st.session_state.pagination_page = min(
        st.session_state.pagination_page, 
        n_pages - 1
    )
    
    # Create pagination controls
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("< Previous"):
            st.session_state.pagination_page = max(0, st.session_state.pagination_page - 1)
            st.experimental_rerun()
    
    with col2:
        st.write(f"Page {st.session_state.pagination_page + 1} of {n_pages}")
    
    with col3:
        if st.button("Next >"):
            st.session_state.pagination_page = min(n_pages - 1, st.session_state.pagination_page + 1)
            st.experimental_rerun()
    
    # Get start and end indices for current page
    start_idx = st.session_state.pagination_page * page_size
    end_idx = min(start_idx + page_size, len(df))
    
    # Return the dataframe slice for current page
    return df.iloc[start_idx:end_idx]

def is_mobile():
    """
    Detect if the user is on a mobile device.
    
    Returns:
        bool: True if on mobile, False otherwise
    """
    # Try to get user agent from query params
    try:
        query_params = st.experimental_get_query_params()
        user_agent = query_params.get("user_agent", [""])[0]
        
        # If not available in query params, use a default assumption
        if not user_agent:
            # Default to desktop
            return False
        
        # Check for mobile patterns
        mobile_pattern = r"Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini"
        return bool(re.search(mobile_pattern, user_agent))
    except:
        # Default to desktop on error
        return False

def responsive_columns(ratios=None, mobile_stack=True):
    """
    Create responsive columns that adapt to mobile view.
    
    Args:
        ratios: List of column width ratios (e.g., [1, 2, 1])
        mobile_stack: Whether to stack columns on mobile
        
    Returns:
        list: List of column objects
    """
    # Default to equal ratios if not specified
    if not ratios:
        ratios = [1, 1]
    
    # Check for mobile
    on_mobile = is_mobile()
    
    if on_mobile and mobile_stack:
        # Return each column at full width for mobile
        return [st.container() for _ in ratios]
    else:
        # Use specified ratios for desktop
        return st.columns(ratios)

def responsive_layout(content_func, sidebar_func=None, mobile_sidebar_top=True):
    """
    Create a responsive layout with optional sidebar.
    
    Args:
        content_func: Function to render main content
        sidebar_func: Function to render sidebar content
        mobile_sidebar_top: Whether to show sidebar at top on mobile
        
    Returns:
        None
    """
    # Check for mobile
    on_mobile = is_mobile()
    
    if on_mobile:
        if sidebar_func and mobile_sidebar_top:
            with st.container():
                sidebar_func()
            content_func()
        elif sidebar_func:
            content_func()
            with st.container():
                sidebar_func()
        else:
            content_func()
    else:
        # Desktop layout with sidebar
        if sidebar_func:
            with st.sidebar:
                sidebar_func()
        content_func()

def responsive_table(data, height=None, use_container_width=True):
    """
    Display a table responsively based on device.
    
    Args:
        data: Pandas DataFrame to display
        height: Optional height for desktop
        use_container_width: Whether to use full container width
        
    Returns:
        None
    """
    # Check for mobile
    on_mobile = is_mobile()
    
    if on_mobile:
        # Simpler table for mobile
        st.dataframe(
            data,
            use_container_width=True,
            height=300 if height is None else height
        )
    else:
        # Full-featured table for desktop
        st.dataframe(
            data,
            use_container_width=use_container_width,
            height=None if height is None else height
        )

def add_responsive_css():
    """Add responsive CSS to adjust UI for different screen sizes."""
    st.markdown("""
    <style>
    /* Responsive CSS */
    @media (max-width: 768px) {
        /* Adjust header size on mobile */
        .main h1 {
            font-size: 1.8rem !important;
        }
        .main h2 {
            font-size: 1.5rem !important;
        }
        .main h3 {
            font-size: 1.2rem !important;
        }
        
        /* Adjust container padding */
        .main .block-container {
            padding: 1rem !important;
        }
        
        /* Make buttons more tappable */
        button {
            min-height: 44px !important;
        }
        
        /* Stack widgets */
        div[data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            flex: 0 0 100% !important;
            margin-bottom: 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)