"""
Responsive design utilities.
Enhance mobile experience for Streamlit applications.
"""

import streamlit as st
import re
import platform
from datetime import datetime

def get_device_type():
    """
    Detect device type from user agent.
    
    Returns:
        str: 'mobile', 'tablet', or 'desktop'
    """
    # Get User-Agent string if available
    try:
        user_agent = st.session_state.get('_user_agent', '')
        if not user_agent and hasattr(st, 'get_user_info'):
            user_info = st.get_user_info()
            user_agent = user_info.get('userAgent', '')
            st.session_state['_user_agent'] = user_agent
    except:
        user_agent = ''
    
    # Check if a mobile device
    if re.search(r'Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini', user_agent):
        # Check if tablet
        if re.search(r'iPad|Android(?!.*Mobile)', user_agent):
            return 'tablet'
        return 'mobile'
    return 'desktop'

def get_viewport_width():
    """
    Get estimated viewport width.
    
    Returns:
        int: Estimated viewport width in pixels
    """
    device_type = get_device_type()
    if device_type == 'mobile':
        return 375
    elif device_type == 'tablet':
        return 768
    return 1200

def add_responsive_css():
    """Add responsive CSS to Streamlit app."""
    st.markdown("""
    <style>
    /* Base responsive styles */
    @media screen and (max-width: 640px) {
        /* Make fonts more readable on mobile */
        .stMarkdown p, .stMarkdown li {
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        
        /* Increase button size on mobile */
        button[kind="primary"] {
            height: 3rem !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* Adjust form fields */
        .stTextInput input, .stSelectbox select, 
        .stMultiselect div[data-baseweb="select"] {
            font-size: 16px !important; /* Prevents iOS zoom */
            height: 3rem !important;
        }
        
        /* Adjust metric display */
        div[data-testid="metric-container"] {
            padding: 0.5rem !important;
        }
        
        /* Adjust spacing */
        div[data-testid="stVerticalBlock"] > div {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        /* Make tables scroll horizontally */
        div[data-testid="stTable"], .stDataFrame {
            overflow-x: auto !important;
        }
        
        /* Adjust visualization size */
        div[data-testid="stChart"] {
            max-width: 100% !important;
            overflow-x: auto !important;
        }
    }
    
    /* Additional tablet styles */
    @media screen and (min-width: 641px) and (max-width: 1024px) {
        /* Adjust for tablets */
        div[data-testid="stVerticalBlock"] > div {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def responsive_columns(num_columns=2, content_list=None):
    """
    Create responsive columns that adjust based on device.
    
    Args:
        num_columns: Default number of columns for desktop
        content_list: Optional list of content functions to display
        
    Returns:
        list: List of column objects
    """
    device_type = get_device_type()
    
    # Adjust columns based on device
    if device_type == 'mobile':
        actual_columns = 1  # Single column on mobile
    elif device_type == 'tablet':
        actual_columns = min(2, num_columns)  # Max 2 columns on tablet
    else:
        actual_columns = num_columns  # Use specified columns on desktop
    
    # Create columns
    columns = st.columns(actual_columns)
    
    # If content is provided, distribute it
    if content_list:
        for i, content_func in enumerate(content_list):
            with columns[i % actual_columns]:
                content_func()
                
    return columns

def responsive_metric_rows(metrics, columns_desktop=4):
    """
    Display metrics in a responsive grid.
    
    Args:
        metrics: List of dicts with 'label', 'value', and optional 'delta'
        columns_desktop: Number of columns on desktop
    """
    device_type = get_device_type()
    
    # Determine columns based on device
    if device_type == 'mobile':
        columns_count = 2
    elif device_type == 'tablet':
        columns_count = 3
    else:
        columns_count = columns_desktop
    
    # Create rows of metrics
    for i in range(0, len(metrics), columns_count):
        row_metrics = metrics[i:i+columns_count]
        cols = st.columns(len(row_metrics))
        
        for j, metric in enumerate(row_metrics):
            with cols[j]:
                if 'delta' in metric:
                    st.metric(
                        label=metric['label'],
                        value=metric['value'],
                        delta=metric['delta']
                    )
                else:
                    st.metric(
                        label=metric['label'],
                        value=metric['value']
                    )

def responsive_form(title, key, fields, submit_label="Submit"):
    """
    Create a responsive form with proper mobile styling.
    
    Args:
        title: Form title
        key: Unique form key
        fields: List of field dicts with 'type', 'key', 'label', and 'options' for select
        submit_label: Text for submit button
        
    Returns:
        dict: Form values after submission
    """
    device_type = get_device_type()
    
    # Apply different styling based on device
    if device_type == 'mobile':
        st.markdown(f"### {title}")
    else:
        st.subheader(title)
    
    # Create form
    with st.form(key=key):
        values = {}
        
        for field in fields:
            field_type = field['type']
            field_key = field['key']
            field_label = field['label']
            
            # Apply different styling for mobile
            if device_type == 'mobile':
                field_label = f"<p style='margin-bottom:4px;font-weight:500;'>{field_label}</p>"
                st.markdown(field_label, unsafe_allow_html=True)
            
            # Create appropriate input type
            if field_type == 'text':
                values[field_key] = st.text_input(
                    "" if device_type == 'mobile' else field_label,
                    key=field_key
                )
            elif field_type == 'textarea':
                values[field_key] = st.text_area(
                    "" if device_type == 'mobile' else field_label,
                    key=field_key
                )
            elif field_type == 'number':
                values[field_key] = st.number_input(
                    "" if device_type == 'mobile' else field_label,
                    key=field_key,
                    **{k: v for k, v in field.items() if k in ['min_value', 'max_value', 'value', 'step']}
                )
            elif field_type == 'select':
                values[field_key] = st.selectbox(
                    "" if device_type == 'mobile' else field_label,
                    options=field['options'],
                    key=field_key,
                    index=field.get('index', 0)
                )
            elif field_type == 'date':
                values[field_key] = st.date_input(
                    "" if device_type == 'mobile' else field_label,
                    key=field_key,
                    value=field.get('value', datetime.now().date())
                )
            elif field_type == 'checkbox':
                values[field_key] = st.checkbox(
                    field_label,
                    key=field_key,
                    value=field.get('value', False)
                )
            
            # Add spacing for mobile
            if device_type == 'mobile':
                st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)
        
        # Submit button
        if device_type == 'mobile':
            st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button(
                submit_label,
                use_container_width=True
            )
        else:
            submit = st.form_submit_button(submit_label)
            
        if submit:
            return values
        
        return None

def responsive_table(data, pagination=True, page_size=10):
    """
    Display a table that's responsive on mobile devices.
    
    Args:
        data: DataFrame or list of dicts
        pagination: Whether to paginate results
        page_size: Number of items per page
    """
    import pandas as pd
    
    # Convert to DataFrame if it's a list
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    
    device_type = get_device_type()
    
    # For mobile, we might want to limit columns or reformat
    if device_type == 'mobile':
        # Add horizontal scrolling wrapper
        st.markdown("""
        <style>
        div[data-testid="stTable"] {
            width: 100%;
            overflow-x: auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Optionally limit columns on very small screens
        if data.shape[1] > 4:
            # Show a warning
            st.markdown("<small>Scroll horizontally to see all columns</small>", unsafe_allow_html=True)
    
    # Paginate if needed
    if pagination and len(data) > page_size:
        # Create pagination controls
        max_pages = (len(data) + page_size - 1) // page_size
        
        # Store current page in session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0
            
        # Pagination controls
        col1, col2, col3 = responsive_columns(3)
        
        with col1:
            if st.button("← Previous", disabled=st.session_state.current_page <= 0):
                st.session_state.current_page -= 1
                st.experimental_rerun()
                
        with col2:
            st.markdown(f"<div style='text-align:center'>Page {st.session_state.current_page + 1}/{max_pages}</div>", unsafe_allow_html=True)
            
        with col3:
            if st.button("Next →", disabled=st.session_state.current_page >= max_pages - 1):
                st.session_state.current_page += 1
                st.experimental_rerun()
        
        # Get current page slice
        start_idx = st.session_state.current_page * page_size
        end_idx = min(start_idx + page_size, len(data))
        data_to_show = data.iloc[start_idx:end_idx]
    else:
        data_to_show = data
    
    # Display the table
    st.dataframe(data_to_show)