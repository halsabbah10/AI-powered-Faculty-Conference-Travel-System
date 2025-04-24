"""
Pytest configuration for end-to-end tests.
"""

import os
import pytest
import sys
import subprocess
import time
import signal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(scope="session", autouse=True)
def setup_test_app():
    """Start the Streamlit app for testing if it's not already running."""
    # Check if we should use an existing app instance
    if os.getenv("TEST_APP_URL"):
        # Use existing app
        yield
        return
    
    # Start a test instance of the app
    print("Starting test instance of the app...")
    
    # Set environment variables for test
    env = os.environ.copy()
    env["DB_NAME"] = "con_system_test"
    env["PORT"] = "8501"
    env["TESTING"] = "true"
    
    # Start streamlit
    process = subprocess.Popen(
        ["streamlit", "run", "app/main.py"], 
        env=env,
        start_new_session=True  # This helps with proper cleanup
    )
    
    # Wait for app to start
    time.sleep(5)
    
    # Return to tests
    yield
    
    # Cleanup
    print("Stopping test instance of the app...")
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)