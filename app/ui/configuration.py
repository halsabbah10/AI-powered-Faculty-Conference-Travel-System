"""
System configuration module.
Provides UI for configuring application settings.
"""

import streamlit as st
import os
import json
import logging
from datetime import datetime

from app.ui.common import display_header, display_success_box, display_error_box
from app.utils.feature_flags import FeatureFlags
from app.database.connection import DatabaseManager

def show_configuration_panel():
    """Display system configuration panel."""
    display_header("System Configuration")
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "General Settings", 
        "AI Configuration", 
        "Monitoring Settings",
        "Database Settings"
    ])
    
    with tab1:
        show_general_settings()
    
    with tab2:
        show_ai_configuration()
    
    with tab3:
        show_monitoring_settings()
    
    with tab4:
        show_database_settings()

def show_general_settings():
    """Display general application settings."""
    st.subheader("General Application Settings")
    
    # Load current settings
    config_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config",
        "app_settings.json"
    )
    
    # Create default settings if file doesn't exist
    if not os.path.exists(config_file):
        default_settings = {
            "app_name": "Faculty Conference Travel System",
            "session_timeout_minutes": 30,
            "max_upload_size_mb": 10,
            "enable_email_notifications": False,
            "default_per_diem_rate": 200,
            "updated_at": datetime.now().isoformat()
        }
        
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_settings, f, indent=2)
    
    # Load settings
    with open(config_file, 'r') as f:
        settings = json.load(f)
    
    # Display last update time
    st.info(f"Last updated: {settings.get('updated_at', 'Unknown')}")
    
    # Create settings form
    with st.form("general_settings_form"):
        app_name = st.text_input(
            "Application Name",
            value=settings.get("app_name", "Faculty Conference Travel System")
        )
        
        session_timeout = st.number_input(
            "Session Timeout (minutes)",
            min_value=5,
            max_value=120,
            value=settings.get("session_timeout_minutes", 30)
        )
        
        max_upload_size = st.number_input(
            "Maximum Upload Size (MB)",
            min_value=1,
            max_value=100,
            value=settings.get("max_upload_size_mb", 10)
        )
        
        enable_email = st.checkbox(
            "Enable Email Notifications",
            value=settings.get("enable_email_notifications", False)
        )
        
        default_per_diem = st.number_input(
            "Default Per Diem Rate ($)",
            min_value=0.0,
            max_value=1000.0,
            value=settings.get("default_per_diem_rate", 200.0)
        )
        
        submitted = st.form_submit_button("Save Settings")
        
        if submitted:
            try:
                # Update settings
                settings.update({
                    "app_name": app_name,
                    "session_timeout_minutes": session_timeout,
                    "max_upload_size_mb": max_upload_size,
                    "enable_email_notifications": enable_email,
                    "default_per_diem_rate": default_per_diem,
                    "updated_at": datetime.now().isoformat()
                })
                
                # Save settings
                with open(config_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                # Update environment variable
                if enable_email:
                    os.environ["EMAIL_ENABLED"] = "True"
                else:
                    os.environ["EMAIL_ENABLED"] = "False"
                
                display_success_box("Settings updated successfully!")
                
            except Exception as e:
                logging.error(f"Error saving settings: {str(e)}")
                display_error_box(f"Error saving settings: {str(e)}")

def show_ai_configuration():
    """Display AI service configuration."""
    st.subheader("AI Service Configuration")
    
    # AI provider selection
    provider = st.selectbox(
        "AI Provider",
        options=["OpenAI", "Google AI"],
        index=0 if os.getenv("AI_PROVIDER", "openai").lower() == "openai" else 1
    )
    
    # OpenAI settings
    if provider == "OpenAI":
        st.subheader("OpenAI Configuration")
        
        api_key = st.text_input(
            "OpenAI API Key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password"
        )
        
        model = st.selectbox(
            "OpenAI Model",
            options=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            index=0 if os.getenv("OPENAI_MODEL", "gpt-3.5-turbo") == "gpt-3.5-turbo" else 
                  (1 if os.getenv("OPENAI_MODEL") == "gpt-4" else 2)
        )
    
    # Google AI settings
    else:
        st.subheader("Google AI Configuration")
        
        api_key = st.text_input(
            "Google AI API Key",
            value=os.getenv("GOOGLE_AI_API_KEY", ""),
            type="password"
        )
        
        model = st.selectbox(
            "Google AI Model",
            options=["gemini-pro", "gemini-ultra"],
            index=0 if os.getenv("GOOGLE_AI_MODEL", "gemini-pro") == "gemini-pro" else 1
        )
    
    # Feature flag status for AI features
    st.subheader("AI Feature Configuration")
    
    ai_analysis_enabled = st.checkbox(
        "Enable AI Analysis",
        value=FeatureFlags.is_enabled("ai_analysis")
    )
    
    # Save button
    if st.button("Save AI Configuration"):
        try:
            # Set environment variables
            if provider == "OpenAI":
                os.environ["AI_PROVIDER"] = "openai"
                os.environ["OPENAI_API_KEY"] = api_key
                os.environ["OPENAI_MODEL"] = model
            else:
                os.environ["AI_PROVIDER"] = "google"
                os.environ["GOOGLE_AI_API_KEY"] = api_key
                os.environ["GOOGLE_AI_MODEL"] = model
            
            # Update feature flags
            FeatureFlags.update_flag(
                "ai_analysis",
                enabled=ai_analysis_enabled
            )
            
            # Save to .env.local file for persistence
            env_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                ".env.local"
            )
            
            with open(env_file, 'w') as f:
                f.write(f"AI_PROVIDER={provider.lower()}\n")
                if provider == "OpenAI":
                    f.write(f"OPENAI_API_KEY={api_key}\n")
                    f.write(f"OPENAI_MODEL={model}\n")
                else:
                    f.write(f"GOOGLE_AI_API_KEY={api_key}\n")
                    f.write(f"GOOGLE_AI_MODEL={model}\n")
            
            display_success_box("AI configuration saved successfully!")
            
        except Exception as e:
            logging.error(f"Error saving AI configuration: {str(e)}")
            display_error_box(f"Error saving AI configuration: {str(e)}")

def show_monitoring_settings():
    """Display monitoring and logging settings."""
    st.subheader("Monitoring & Logging Configuration")
    
    # Error tracking configuration
    st.subheader("Error Tracking")
    
    error_tracking_enabled = st.checkbox(
        "Enable External Error Tracking",
        value=os.getenv("ERROR_TRACKING_ENABLED", "false").lower() == "true"
    )
    
    if error_tracking_enabled:
        error_tracking_url = st.text_input(
            "Error Tracking Service URL",
            value=os.getenv("ERROR_TRACKING_URL", "")
        )
        
        error_tracking_key = st.text_input(
            "Error Tracking API Key",
            value=os.getenv("ERROR_TRACKING_KEY", ""),
            type="password"
        )
        
        error_tracking_project = st.text_input(
            "Project Name",
            value=os.getenv("ERROR_TRACKING_PROJECT", "ftcs")
        )
    
    # Performance monitoring settings
    st.subheader("Performance Monitoring")
    
    perf_history_days = st.slider(
        "Days to retain performance metrics",
        min_value=1,
        max_value=30,
        value=7
    )
    
    slow_query_threshold = st.number_input(
        "Slow query threshold (seconds)",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1
    )
    
    # Log level settings
    st.subheader("Logging Configuration")
    
    log_level = st.selectbox(
        "Log Level",
        options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        index=1  # Default to INFO
    )
    
    # Save button
    if st.button("Save Monitoring Configuration"):
        try:
            # Set environment variables
            os.environ["ERROR_TRACKING_ENABLED"] = str(error_tracking_enabled).lower()
            if error_tracking_enabled:
                os.environ["ERROR_TRACKING_URL"] = error_tracking_url
                os.environ["ERROR_TRACKING_KEY"] = error_tracking_key
                os.environ["ERROR_TRACKING_PROJECT"] = error_tracking_project
            
            os.environ["PERF_HISTORY_DAYS"] = str(perf_history_days)
            os.environ["SLOW_QUERY_THRESHOLD"] = str(slow_query_threshold)
            os.environ["LOG_LEVEL"] = log_level
            
            # Update logging configuration
            logging.getLogger().setLevel(getattr(logging, log_level))
            
            # Save to .env.local file for persistence
            env_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                ".env.local"
            )
            
            # Read existing content
            existing_content = ""
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    existing_content = f.read()
            
            # Update or add monitoring settings
            with open(env_file, 'w') as f:
                f.write(existing_content)
                f.write(f"\nERROR_TRACKING_ENABLED={str(error_tracking_enabled).lower()}\n")
                if error_tracking_enabled:
                    f.write(f"ERROR_TRACKING_URL={error_tracking_url}\n")
                    f.write(f"ERROR_TRACKING_KEY={error_tracking_key}\n")
                    f.write(f"ERROR_TRACKING_PROJECT={error_tracking_project}\n")
                
                f.write(f"PERF_HISTORY_DAYS={perf_history_days}\n")
                f.write(f"SLOW_QUERY_THRESHOLD={slow_query_threshold}\n")
                f.write(f"LOG_LEVEL={log_level}\n")
            
            display_success_box("Monitoring configuration saved successfully!")
            
        except Exception as e:
            logging.error(f"Error saving monitoring configuration: {str(e)}")
            display_error_box(f"Error saving monitoring configuration: {str(e)}")

def show_database_settings():
    """Display database configuration and maintenance options."""
    st.subheader("Database Configuration")
    
    # Current database connection info
    st.info("""
    This section shows the current database connection and allows for 
    maintenance operations. Changing the connection details requires 
    application restart.
    """)
    
    # Display current database info
    cols = st.columns(4)
    cols[0].metric("Host", os.getenv("DB_HOST", "localhost"))
    cols[1].metric("Database", os.getenv("DB_NAME", "con_system"))
    cols[2].metric("User", os.getenv("DB_USER", "root"))
    cols[3].metric("Port", os.getenv("DB_PORT", "3306"))
    
    # Database maintenance
    st.subheader("Database Maintenance")
    
    maintenance_option = st.selectbox(
        "Maintenance Operation",
        options=[
            "Test Connection",
            "Optimize Tables",
            "Backup Database",
            "Run Database Migrations"
        ]
    )
    
    if st.button("Execute"):
        if maintenance_option == "Test Connection":
            try:
                conn = DatabaseManager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                display_success_box("Database connection successful!")
            except Exception as e:
                logging.error(f"Database connection error: {str(e)}")
                display_error_box(f"Database connection error: {str(e)}")
                
        elif maintenance_option == "Optimize Tables":
            try:
                # Get list of tables
                tables = DatabaseManager.execute_query(
                    "SHOW TABLES"
                )
                
                # Extract table names
                table_names = [list(table.values())[0] for table in tables]
                
                # Optimize each table
                for table in table_names:
                    DatabaseManager.execute_query(
                        f"OPTIMIZE TABLE `{table}`",
                        fetch=False
                    )
                
                display_success_box(f"Successfully optimized {len(table_names)} tables!")
                
            except Exception as e:
                logging.error(f"Database optimization error: {str(e)}")
                display_error_box(f"Database optimization error: {str(e)}")
                
        elif maintenance_option == "Backup Database":
            st.info("Database backup functionality would be implemented here.")
            # In a real implementation, this would trigger a database dump
            # using mysqldump or a similar tool
                
        elif maintenance_option == "Run Database Migrations":
            try:
                # Import and run migrations
                from migrations.migrate import main as run_migrations
                
                # Run migrations
                run_migrations(["migrate"])
                
                display_success_box("Database migrations completed successfully!")
                
            except Exception as e:
                logging.error(f"Database migration error: {str(e)}")
                display_error_box(f"Database migration error: {str(e)}")