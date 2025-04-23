"""
Pytest configuration file for the test suite.
"""

import os
import sys
import pytest
import mysql.connector
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app modules
from app.database.connection import DatabaseManager
from app.utils.security import hash_password

# Test database configuration
TEST_DB_CONFIG = {
    "host": os.getenv("TEST_DB_HOST", "localhost"),
    "user": os.getenv("TEST_DB_USER", "root"),
    "password": os.getenv("TEST_DB_PASSWORD", "root"),
    "database": os.getenv("TEST_DB_NAME", "con_system_test")
}

@pytest.fixture(scope="session")
def setup_test_database():
    """
    Set up a test database for unit tests.
    This creates a separate database specifically for testing.
    """
    # Connect to MySQL server (without specifying database)
    conn = mysql.connector.connect(
        host=TEST_DB_CONFIG["host"],
        user=TEST_DB_CONFIG["user"],
        password=TEST_DB_CONFIG["password"]
    )
    cursor = conn.cursor()
    
    try:
        # Drop test database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_CONFIG['database']}")
        
        # Create test database
        cursor.execute(f"CREATE DATABASE {TEST_DB_CONFIG['database']}")
        
        # Use the test database
        cursor.execute(f"USE {TEST_DB_CONFIG['database']}")
        
        # Load schema from SQL file
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'con_system.sql')
        with open(schema_file, 'r') as f:
            sql_commands = f.read().split(';')
            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
        
        conn.commit()
        
        # Insert test data
        # Create test users
        cursor.execute(
            """
            INSERT INTO faculty (user_id, name, email, department, role, password)
            VALUES 
            ('test_prof', 'Test Professor', 'prof@test.com', 'Computer Science', 'professor', %s),
            ('test_acct', 'Test Accountant', 'acct@test.com', 'Finance', 'accountant', %s),
            ('test_appr', 'Test Approver', 'appr@test.com', 'Administration', 'approval', %s)
            """,
            (hash_password('testpass'), hash_password('testpass'), hash_password('testpass'))
        )
        
        # Create test budget
        current_year = datetime.now().year
        cursor.execute(
            """
            INSERT INTO budget (budget_year, amount, created_by, creation_date)
            VALUES (%s, 50000.00, 'test_acct', NOW())
            """,
            (current_year,)
        )
        
        # Create test request
        cursor.execute(
            """
            INSERT INTO requests (
                request_id, faculty_user_id, conference_name, purpose_of_attending,
                conference_url, destination, city, date_from, date_to,
                per_diem, registration_fee, visa_fee, status
            )
            VALUES (
                'TEST-REQ-001', 'test_prof', 'Test Conference', 'Presenting a Paper',
                'http://test-conference.com', 'United States', 'New York',
                DATE_ADD(CURDATE(), INTERVAL 30 DAY), DATE_ADD(CURDATE(), INTERVAL 35 DAY),
                200.00, 500.00, 0.00, 'pending'
            )
            """
        )
        
        conn.commit()
        
        # Return the connection for cleanup
        return conn
        
    except Exception as e:
        print(f"Error setting up test database: {str(e)}")
        if conn:
            conn.rollback()
        raise

@pytest.fixture(scope="function")
def test_db_connection(setup_test_database):
    """
    Create a test database connection for each test.
    """
    # Override the database configuration for tests
    original_config = DatabaseManager.db_config.copy()
    DatabaseManager.db_config = TEST_DB_CONFIG
    
    yield
    
    # Restore original configuration
    DatabaseManager.db_config = original_config

@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state for testing."""
    import streamlit as st
    
    # Save original session state
    original_session_state = st.session_state
    
    # Create a new session state
    class MockSessionState(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
        def __getattr__(self, key):
            if key in self:
                return self[key]
            return None
            
        def __setattr__(self, key, value):
            self[key] = value
    
    # Replace session state with mock
    st.session_state = MockSessionState()
    
    # Set default values
    st.session_state.logged_in_user = "test_prof"
    st.session_state.user_name = "Test Professor"
    st.session_state.user_role = "professor"
    st.session_state.login_time = datetime.now()
    
    yield st.session_state
    
    # Restore original session state
    st.session_state = original_session_state