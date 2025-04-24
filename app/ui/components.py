"""
UI Components module.
Provides reusable UI components for the application.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import time
from functools import wraps
from app.utils.internationalization import t
from app.ui.common import display_error_box, display_info_box, display_success_box
from app.utils.validation import Validator, display_form_errors

def with_loading_spinner(func):
    """
    Decorator to display a loading spinner while a function executes.
    
    Args:
        func: Function to wrap with loading spinner
    
    Returns:
        Wrapped function with loading spinner
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with st.spinner(t("common.loading", "Loading...")):
            return func(*args, **kwargs)
    return wrapper

def card_container(title=None, key=None, padding="1rem", border_radius="0.5rem", border_color="#E5E7EB"):
    """
    Create a card container with styling.
    
    Args:
        title: Optional card title
        key: Optional key for the container
        padding: CSS padding value
        border_radius: CSS border radius value
        border_color: CSS border color value
    
    Returns:
        Streamlit container object
    """
    container = st.container(key=key)
    
    # Generate unique key for this card
    if key is None:
        key = f"card_{int(time.time() * 1000)}"
    
    # Apply card styling
    with container:
        st.markdown(f"""
        <div style="
            padding: {padding}; 
            border-radius: {border_radius}; 
            border: 1px solid {border_color};
            margin-bottom: 1rem;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        ">
        """, unsafe_allow_html=True)
        
        # Add title if provided
        if title:
            st.markdown(f"<h3 style='margin-top: 0;'>{title}</h3>", unsafe_allow_html=True)
    
    # Close card div at the end
    container.markdown("</div>", unsafe_allow_html=True)
    
    return container

def status_badge(status):
    """
    Create a styled status badge.
    
    Args:
        status: Status string ('pending', 'approved', 'rejected', etc.)
        
    Returns:
        str: HTML for the status badge
    """
    status = status.lower()
    
    if status == 'approved':
        color = '#d4edda'
        text_color = '#155724'
    elif status == 'rejected':
        color = '#f8d7da'
        text_color = '#721c24'
    elif status == 'pending':
        color = '#fff3cd'
        text_color = '#856404'
    else:
        color = '#e2e8f0'
        text_color = '#1a202c'
    
    return f"""
    <span style="
        background-color: {color}; 
        color: {text_color}; 
        padding: 0.25rem 0.5rem; 
        border-radius: 0.25rem; 
        font-size: 0.875rem;
        font-weight: 600;
    ">
        {status.capitalize()}
    </span>
    """

def show_request_listing(requests, show_user=True, show_actions=False, on_view=None, on_approve=None, on_reject=None):
    """
    Display a formatted request listing with options.
    
    Args:
        requests: List of request dictionaries
        show_user: Whether to show user information
        show_actions: Whether to show action buttons
        on_view: Optional callback when View button is clicked
        on_approve: Optional callback when Approve button is clicked
        on_reject: Optional callback when Reject button is clicked
    """
    if not requests:
        st.info(t("common.no_records", "No records found"))
        return
    
    # Create dataframe for display
    df = pd.DataFrame(requests)
    
    # Format for display
    display_df = df.copy()
    
    # Format dates
    if 'date_created' in display_df.columns:
        display_df['date_created'] = pd.to_datetime(display_df['date_created']).dt.strftime('%Y-%m-%d')
    
    if 'date_from' in display_df.columns and 'date_to' in display_df.columns:
        display_df['travel_dates'] = (
            pd.to_datetime(display_df['date_from']).dt.strftime('%Y-%m-%d') + 
            ' to ' + 
            pd.to_datetime(display_df['date_to']).dt.strftime('%Y-%m-%d')
        )
    
    # Format status with badges
    if 'status' in display_df.columns:
        display_df['status'] = display_df['status'].apply(
            lambda x: status_badge(x)
        )
    
    # Set columns to display
    display_columns = ['status', 'conference_name', 'destination']
    
    if 'travel_dates' in display_df.columns:
        display_columns.append('travel_dates')
    
    if show_user and 'name' in display_df.columns:
        display_columns.insert(1, 'name')
    
    if 'total_cost' in display_df.columns:
        display_df['total_cost'] = display_df['total_cost'].apply(
            lambda x: f"${x:,.2f}" if x else "$0.00"
        )
        display_columns.append('total_cost')
    
    # Display the dataframe
    st.write(display_df[display_columns].to_html(escape=False), unsafe_allow_html=True)
    
    # Action buttons
    if show_actions and len(requests) > 0:
        st.write("### Actions")
        
        for i, request in enumerate(requests):
            cols = st.columns(4 if on_approve and on_reject else 2)
            
            with cols[0]:
                st.write(f"**{request.get('conference_name', 'Request')}**")
            
            with cols[1]:
                if on_view and st.button(t("common.view", "View"), key=f"view_{request['request_id']}"):
                    on_view(request)
            
            if on_approve and on_reject:
                with cols[2]:
                    if request.get('status') == 'pending' and st.button(
                        t("approval.approve", "Approve"), 
                        key=f"approve_{request['request_id']}"
                    ):
                        on_approve(request)
                
                with cols[3]:
                    if request.get('status') == 'pending' and st.button(
                        t("approval.reject", "Reject"), 
                        key=f"reject_{request['request_id']}"
                    ):
                        on_reject(request)

def show_request_details(request, show_approval_actions=False, on_approve=None, on_reject=None):
    """
    Display detailed request information.
    
    Args:
        request: Request dictionary
        show_approval_actions: Whether to show approval/rejection actions
        on_approve: Optional callback when approved
        on_reject: Optional callback when rejected
    """
    if not request:
        st.info(t("common.not_found", "Request not found"))
        return
    
    # Create two columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(t("request.details", "Request Details"))
        
        st.write(f"**{t('request.id', 'Request ID')}:** {request.get('request_id', 'N/A')}")
        st.write(f"**{t('request.status', 'Status')}:** {request.get('status', 'Unknown').capitalize()}")
        st.write(f"**{t('request.created', 'Created')}:** {request.get('date_created', 'Unknown')}")
        
        if request.get('approved_by'):
            st.write(f"**{t('request.approved_by', 'Approved By')}:** {request.get('approved_by', 'Unknown')}")
        
        if request.get('approval_notes'):
            st.write(f"**{t('request.approval_notes', 'Approval Notes')}:** {request.get('approval_notes', 'None')}")
    
    with col2:
        st.subheader(t("request.travel_info", "Travel Information"))
        
        st.write(f"**{t('request.conference', 'Conference')}:** {request.get('conference_name', 'N/A')}")
        st.write(f"**{t('request.destination', 'Destination')}:** {request.get('destination', 'N/A')}, {request.get('city', 'N/A')}")
        st.write(f"**{t('request.dates', 'Dates')}:** {request.get('date_from', 'N/A')} to {request.get('date_to', 'N/A')}")
        
        if request.get('purpose_of_attending'):
            st.write(f"**{t('request.purpose', 'Purpose')}:** {request.get('purpose_of_attending', 'N/A')}")
    
    # Budget information
    st.subheader(t("request.budget_info", "Budget Information"))
    
    budget_cols = st.columns(4)
    
    with budget_cols[0]:
        st.metric(
            t("request.registration_fee", "Registration Fee"),
            f"${request.get('registration_fee', 0):,.2f}"
        )
    
    with budget_cols[1]:
        st.metric(
            t("request.per_diem", "Per Diem"),
            f"${request.get('per_diem', 0):,.2f}"
        )
    
    with budget_cols[2]:
        st.metric(
            t("request.visa_fee", "Visa Fee"),
            f"${request.get('visa_fee', 0):,.2f}"
        )
    
    with budget_cols[3]:
        st.metric(
            t("request.total_cost", "Total Cost"),
            f"${request.get('total_cost', 0):,.2f}",
            delta=None
        )
    
    # Documents
    if 'documents' in request and request['documents']:
        st.subheader(t("request.documents", "Documents"))
        
        for doc in request['documents']:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{doc.get('file_name', 'Document')}**")
                if doc.get('description'):
                    st.write(doc.get('description'))
            
            with col2:
                st.download_button(
                    t("common.download", "Download"),
                    data=doc.get('file_content', b''),
                    file_name=doc.get('file_name', 'document'),
                    mime=doc.get('file_type', 'application/octet-stream'),
                    key=f"doc_{doc.get('document_id')}"
                )
    
    # Approval actions
    if show_approval_actions and request.get('status') == 'pending':
        st.subheader(t("approval.actions", "Approval Actions"))
        
        with st.form(key=f"approval_form_{request.get('request_id')}"):
            notes = st.text_area(t("approval.notes", "Notes"))
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button(t("approval.approve", "Approve Request")):
                    if on_approve:
                        on_approve(request, notes)
            
            with col2:
                if st.form_submit_button(t("approval.reject", "Reject Request")):
                    if on_reject:
                        on_reject(request, notes)

def display_metric_cards(metrics, num_columns=4):
    """
    Display a row of metric cards.
    
    Args:
        metrics: List of dictionaries with 'label', 'value', and optional 'delta'
        num_columns: Number of columns to display
    """
    cols = st.columns(num_columns)
    
    for i, metric in enumerate(metrics):
        with cols[i % num_columns]:
            st.metric(
                label=metric['label'],
                value=metric['value'],
                delta=metric.get('delta')
            )

def create_bar_chart(data, x, y, title=None, color=None, height=400):
    """
    Create a Plotly bar chart.
    
    Args:
        data: DataFrame with chart data
        x: Column name for X axis
        y: Column name for Y axis
        title: Optional chart title
        color: Optional column for color
        height: Chart height
        
    Returns:
        Plotly figure
    """
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        height=height,
        template='plotly_white'
    )
    
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y,
        legend_title=color if color else None,
        font=dict(
            family="Arial, sans-serif",
            size=12
        )
    )
    
    return fig

def create_line_chart(data, x, y, title=None, color=None, height=400):
    """
    Create a Plotly line chart.
    
    Args:
        data: DataFrame with chart data
        x: Column name for X axis
        y: Column name for Y axis
        title: Optional chart title
        color: Optional column for color
        height: Chart height
        
    Returns:
        Plotly figure
    """
    fig = px.line(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        height=height,
        template='plotly_white',
        markers=True
    )
    
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y,
        legend_title=color if color else None,
        font=dict(
            family="Arial, sans-serif",
            size=12
        )
    )
    
    return fig

def create_pie_chart(data, names, values, title=None, height=400):
    """
    Create a Plotly pie chart.
    
    Args:
        data: DataFrame with chart data
        names: Column name for slice names
        values: Column name for slice values
        title: Optional chart title
        height: Chart height
        
    Returns:
        Plotly figure
    """
    fig = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        height=height,
        template='plotly_white'
    )
    
    fig.update_layout(
        font=dict(
            family="Arial, sans-serif",
            size=12
        )
    )
    
    return fig

def create_form(fields, submit_label="Submit", on_submit=None):
    """
    Create a form with specified fields.
    
    Args:
        fields: List of field dictionaries with the following keys:
            - name: Field name (required)
            - type: Field type (text, number, date, select, etc.)
            - label: Display label
            - required: Whether field is required
            - default: Default value
            - options: List of options for select fields
            - min/max: Min/max values for number fields
            - validators: List of validator functions
        submit_label: Label for submit button
        on_submit: Callback function when form is submitted
        
    Returns:
        tuple: (is_submitted, form_data)
    """
    with st.form("dynamic_form"):
        form_data = {}
        
        for field in fields:
            field_name = field['name']
            field_type = field.get('type', 'text')
            label = field.get('label', field_name.replace('_', ' ').title())
            required = field.get('required', False)
            
            # Add required indicator
            display_label = f"{label} *" if required else label
            
            # Handle different field types
            if field_type == 'text':
                form_data[field_name] = st.text_input(
                    display_label,
                    value=field.get('default', ''),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'number':
                form_data[field_name] = st.number_input(
                    display_label,
                    min_value=field.get('min'),
                    max_value=field.get('max'),
                    value=field.get('default', 0),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'date':
                form_data[field_name] = st.date_input(
                    display_label,
                    value=field.get('default', datetime.now()),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'select':
                form_data[field_name] = st.selectbox(
                    display_label,
                    options=field.get('options', []),
                    index=field.get('default_index', 0),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'multiselect':
                form_data[field_name] = st.multiselect(
                    display_label,
                    options=field.get('options', []),
                    default=field.get('default', []),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'textarea':
                form_data[field_name] = st.text_area(
                    display_label,
                    value=field.get('default', ''),
                    height=field.get('height', 100),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'checkbox':
                form_data[field_name] = st.checkbox(
                    display_label,
                    value=field.get('default', False),
                    key=f"form_{field_name}"
                )
            
            elif field_type == 'file':
                form_data[field_name] = st.file_uploader(
                    display_label,
                    type=field.get('accept', None),
                    key=f"form_{field_name}"
                )
        
        submitted = st.form_submit_button(submit_label)
        
        if submitted and on_submit:
            # Find validators for fields
            validators = {
                field['name']: field.get('validators', [])
                for field in fields
                if 'validators' in field
            }
            
            # Validate form data
            if validators:
                is_valid, errors = Validator.validate_form(form_data, validators)
                
                if not is_valid:
                    display_form_errors(errors)
                    return False, form_data
            
            # Call submission handler
            result = on_submit(form_data)
            if result is False:
                return False, form_data
        
        return submitted, form_data

def show_data_table(data, columns=None, formatting=None, use_container_width=True):
    """
    Display a formatted data table.
    
    Args:
        data: DataFrame or list of dictionaries
        columns: List of columns to include (or None for all)
        formatting: Dictionary of column formatting functions
        use_container_width: Whether to use full container width
    """
    # Convert list to DataFrame if needed
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data
    
    # Filter columns if specified
    if columns:
        df = df[columns]
    
    # Apply formatting
    if formatting:
        formatted_df = df.copy()
        for col, format_func in formatting.items():
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(format_func)
        df = formatted_df
    
    # Display table
    st.dataframe(df, use_container_width=use_container_width)

def show_loading_spinner(func, text="Loading..."):
    """
    Show a loading spinner while executing a function.
    
    Args:
        func: Function to execute
        text: Loading message
        
    Returns:
        Function result
    """
    with st.spinner(text):
        return func()

def show_tabs_with_content(tabs_content):
    """
    Display tabbed content.
    
    Args:
        tabs_content: List of dictionaries with 'title' and 'content' (function)
    """
    if not tabs_content:
        return
    
    # Create tabs
    tabs = st.tabs([tab['title'] for tab in tabs_content])
    
    # Display content in each tab
    for i, tab_content in enumerate(tabs_content):
        with tabs[i]:
            if callable(tab_content.get('content')):
                tab_content['content']()
            elif 'content' in tab_content:
                st.write(tab_content['content'])

def show_confirmation_dialog(title, message, confirm_label="Confirm", cancel_label="Cancel"):
    """
    Display a confirmation dialog.
    
    Args:
        title: Dialog title
        message: Dialog message
        confirm_label: Label for confirm button
        cancel_label: Label for cancel button
        
    Returns:
        bool: True if confirmed, False otherwise
    """
    with st.container():
        st.subheader(title)
        st.write(message)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(confirm_label, key="confirm_dialog"):
                return True
        
        with col2:
            if st.button(cancel_label, key="cancel_dialog"):
                return False
    
    return False