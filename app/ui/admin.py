"""
Admin dashboard module.
Provides administrative functions and monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import json

from app.utils.error_monitoring import ErrorMonitor
from app.ui.common import display_header, display_info_box, display_warning_box
from app.database.queries import get_user_activity_logs

def show_admin_dashboard():
    """Display admin dashboard."""
    display_header("Admin Dashboard")
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["User Activity", "Error Monitoring", "System Status"])
    
    with tab1:
        show_user_activity()
    
    with tab2:
        show_error_monitoring()
    
    with tab3:
        show_system_status()

def show_user_activity():
    """Display user activity logs."""
    st.subheader("User Activity Logs")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=7)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    
    # Convert to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get activity logs
    logs = get_user_activity_logs(start_datetime, end_datetime)
    
    if not logs:
        display_info_box("No activity logs found for the selected period.")
        return
    
    # Display logs
    df = pd.DataFrame(logs)
    
    # Add custom formatting
    st.dataframe(
        df,
        column_config={
            "activity_id": None,  # Hide ID column
            "user_id": "User",
            "activity_type": "Activity",
            "timestamp": st.column_config.DatetimeColumn(
                "Time",
                format="MMM DD, YYYY, hh:mm:ss a"
            ),
            "ip_address": "IP Address",
            "additional_data": "Details"
        },
        use_container_width=True
    )
    
    # Activity summary
    st.subheader("Activity Summary")
    
    # By activity type
    activity_counts = df['activity_type'].value_counts().reset_index()
    activity_counts.columns = ['Activity', 'Count']
    
    fig1 = px.pie(
        activity_counts, 
        values='Count', 
        names='Activity',
        title='Activities by Type'
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # By user
    user_counts = df['user_id'].value_counts().reset_index()
    user_counts.columns = ['User', 'Count']
    
    fig2 = px.bar(
        user_counts, 
        x='User', 
        y='Count',
        title='Activities by User'
    )
    st.plotly_chart(fig2, use_container_width=True)

def show_error_monitoring():
    """Display error monitoring dashboard."""
    st.subheader("Error Monitoring")
    
    # Get errors from local logs
    errors = ErrorMonitor.get_local_errors()
    
    if not errors:
        display_info_box("No errors have been logged.")
        return
    
    # Display error count
    st.metric("Total Errors", len(errors))
    
    # Process errors for display
    error_data = []
    for error in errors:
        error_data.append({
            "error_id": error.get("error_id", "Unknown"),
            "timestamp": error.get("timestamp", ""),
            "type": error.get("type", "Unknown"),
            "message": error.get("message", "No message"),
            "user": error.get("user", {}).get("id", "Anonymous") if error.get("user") else "Anonymous"
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(error_data)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp', ascending=False)
    
    # Display error list
    st.dataframe(
        df,
        column_config={
            "error_id": "Error ID",
            "timestamp": st.column_config.DatetimeColumn(
                "Time",
                format="MMM DD, YYYY, hh:mm:ss a"
            ),
            "type": "Error Type",
            "message": "Message",
            "user": "User"
        },
        use_container_width=True
    )
    
    # Error details
    st.subheader("Error Details")
    
    # Select error to view
    selected_error_id = st.selectbox(
        "Select an error to view details",
        options=[e["error_id"] for e in errors],
        format_func=lambda x: f"{x} - {next((e['type'] for e in errors if e['error_id'] == x), '')}"
    )
    
    if selected_error_id:
        selected_error = next((e for e in errors if e["error_id"] == selected_error_id), None)
        
        if selected_error:
            # Show error details
            cols = st.columns(3)
            cols[0].metric("Error Type", selected_error.get("type", "Unknown"))
            cols[1].metric("Timestamp", datetime.fromisoformat(selected_error.get("timestamp", "")).strftime("%Y-%m-%d %H:%M:%S"))
            cols[2].metric("User", selected_error.get("user", {}).get("id", "Anonymous") if selected_error.get("user") else "Anonymous")
            
            st.subheader("Error Message")
            st.code(selected_error.get("message", "No message"), language="bash")
            
            st.subheader("Traceback")
            tb = selected_error.get("traceback", [])
            if tb:
                for frame in tb:
                    st.code(f"{frame.get('filename', '')}:{frame.get('lineno', '')} - {frame.get('name', '')}\n{frame.get('line', '')}", language="python")
            else:
                st.info("No traceback available")
            
            st.subheader("Additional Data")
            st.json(selected_error.get("additional_data", {}))

def show_system_status():
    """Display system status information."""
    st.subheader("System Status")
    
    # Mock system metrics (in a real implementation, these would come from monitoring tools)
    import psutil
    import platform
    from datetime import datetime, timedelta
    
    # System info
    cols = st.columns(4)
    cols[0].metric("CPU Usage", f"{psutil.cpu_percent()}%")
    cols[1].metric("Memory Usage", f"{psutil.virtual_memory().percent}%")
    cols[2].metric("Disk Usage", f"{psutil.disk_usage('/').percent}%")
    
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"
    cols[3].metric("System Uptime", uptime_str)
    
    # Platform info
    st.subheader("Platform Information")
    platform_info = {
        "System": platform.system(),
        "Node": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Python Version": platform.python_version()
    }
    
    st.json(platform_info)
    
    # Database connection status
    from app.database.connection import DatabaseManager
    
    st.subheader("Database Status")
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        st.success("Database connection is active")
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
    
    # External service status
    st.subheader("External Services")
    
    services = {
        "AI Service": os.getenv("OPENAI_API_KEY") is not None,
        "Email Service": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "Error Tracking": os.getenv("ERROR_TRACKING_ENABLED", "false").lower() == "true"
    }
    
    for service, active in services.items():
        if active:
            st.success(f"{service}: Active")
        else:
            st.warning(f"{service}: Inactive")