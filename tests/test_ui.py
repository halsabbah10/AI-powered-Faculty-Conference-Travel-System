"""
UI testing module.
Tests UI components using pytest and streamlit test utilities.
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Import UI components to test
from app.ui.common import (
    display_header,
    display_info_box,
    display_success_box,
    display_warning_box,
    display_error_box
)
from app.ui.professor import show_submission_form
from app.ui.approval import show_request_review

@pytest.fixture
def mock_streamlit():
    """Mock critical streamlit functions."""
    with patch("streamlit.header") as mock_header, \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.form") as mock_form, \
         patch("streamlit.selectbox") as mock_selectbox, \
         patch("streamlit.text_input") as mock_text_input, \
         patch("streamlit.date_input") as mock_date_input, \
         patch("streamlit.number_input") as mock_number_input, \
         patch("streamlit.file_uploader") as mock_file_uploader, \
         patch("streamlit.form_submit_button") as mock_submit_button:
        
        mock_header.return_value = None
        mock_markdown.return_value = None
        
        mock_form_instance = MagicMock()
        mock_form.return_value.__enter__.return_value = mock_form_instance
        mock_form.return_value.__exit__.return_value = None
        
        mock_selectbox.return_value = "Computer Science"
        mock_text_input.return_value = "Test Input"
        mock_date_input.return_value = datetime.now().date()
        mock_number_input.return_value = 100.0
        
        mock_file = MagicMock()
        mock_file.name = "test.pdf"
        mock_file_uploader.return_value = mock_file
        
        mock_submit_button.return_value = False
        
        yield {
            "header": mock_header,
            "markdown": mock_markdown,
            "form": mock_form,
            "selectbox": mock_selectbox,
            "text_input": mock_text_input,
            "date_input": mock_date_input,
            "number_input": mock_number_input,
            "file_uploader": mock_file_uploader,
            "submit_button": mock_submit_button
        }

@pytest.fixture
def mock_database():
    """Mock database queries."""
    with patch("app.database.queries.get_user_by_id") as mock_get_user, \
         patch("app.database.queries.get_request_by_id") as mock_get_request, \
         patch("app.database.queries.calculate_remaining_budget") as mock_calc_budget, \
         patch("app.database.queries.submit_request") as mock_submit_request:
        
        # Mock user data
        mock_get_user.return_value = {
            "user_id": "test_prof",
            "name": "Test Professor",
            "email": "test@example.com",
            "department": "Computer Science",
            "role": "professor"
        }
        
        # Mock request data
        mock_get_request.return_value = {
            "request_id": "TEST-REQ-001",
            "faculty_user_id": "test_prof",
            "faculty_name": "Test Professor",
            "department": "Computer Science",
            "conference_name": "Test Conference",
            "purpose_of_attending": "Presenting research",
            "conference_url": "https://test-conference.com",
            "destination": "United States",
            "city": "New York",
            "date_from": datetime.now().date() + timedelta(days=30),
            "date_to": datetime.now().date() + timedelta(days=35),
            "per_diem": 200.0,
            "registration_fee": 500.0,
            "visa_fee": 0.0,
            "status": "pending",
            "created_at": datetime.now() - timedelta(days=5),
            "approval_date": None,
            "approval_notes": None
        }
        
        # Mock budget calculation
        mock_calc_budget.return_value = (50000.0, 10000.0, 40000.0)  # total, spent, remaining
        
        # Mock request submission
        mock_submit_request.return_value = "TEST-REQ-002"
        
        yield {
            "get_user": mock_get_user,
            "get_request": mock_get_request,
            "calc_budget": mock_calc_budget,
            "submit_request": mock_submit_request
        }

def test_display_header(mock_streamlit):
    """Test the header display component."""
    display_header("Test Header")
    mock_streamlit["header"].assert_called_once_with("Test Header")

def test_display_info_box(mock_streamlit):
    """Test info box display."""
    display_info_box("Test info message")
    mock_streamlit["markdown"].assert_called_with(
        '<div class="info-box">Test info message</div>',
        unsafe_allow_html=True
    )

def test_display_success_box(mock_streamlit):
    """Test success box display."""
    display_success_box("Test success message")
    mock_streamlit["markdown"].assert_called_with(
        '<div class="success-box">Test success message</div>',
        unsafe_allow_html=True
    )

def test_display_warning_box(mock_streamlit):
    """Test warning box display."""
    display_warning_box("Test warning message")
    mock_streamlit["markdown"].assert_called_with(
        '<div class="warning-box">Test warning message</div>',
        unsafe_allow_html=True
    )

def test_display_error_box(mock_streamlit):
    """Test error box display."""
    display_error_box("Test error message")
    mock_streamlit["markdown"].assert_called_with(
        '<div class="error-box">Test error message</div>',
        unsafe_allow_html=True
    )

@pytest.mark.parametrize("show_logout", [True, False])
def test_header_with_logout(mock_streamlit, show_logout):
    """Test header with logout option."""
    with patch("streamlit.sidebar") as mock_sidebar:
        sidebar_instance = MagicMock()
        mock_sidebar.return_value.__enter__.return_value = sidebar_instance
        
        display_header("Test Header", show_logout=show_logout)
        mock_streamlit["header"].assert_called_once_with("Test Header")

@patch("app.ui.professor.st.session_state", {"logged_in_user": "test_prof"})
def test_show_submission_form(mock_streamlit, mock_database):
    """Test the professor submission form."""
    with patch("app.ui.professor.display_info_box") as mock_info_box:
        # Set up the session state
        st.session_state.logged_in_user = "test_prof"
        
        # Call the function
        show_submission_form()
        
        # Verify form components were created
        mock_streamlit["form"].assert_called()
        mock_streamlit["text_input"].assert_called()
        mock_streamlit["date_input"].assert_called()
        mock_streamlit["number_input"].assert_called()
        mock_streamlit["file_uploader"].assert_called()
        
        # Verify user data was retrieved
        mock_database["get_user"].assert_called_with("test_prof")

@patch("app.ui.approval.st.session_state", {"logged_in_user": "test_appr"})
def test_show_request_review(mock_streamlit, mock_database):
    """Test the request review interface."""
    with patch("app.ui.approval.display_info_box") as mock_info_box, \
         patch("app.ui.approval.st.columns") as mock_columns:
        
        # Set up column mocks
        col1 = MagicMock()
        col2 = MagicMock()
        mock_columns.return_value = [col1, col2]
        
        # Call the function with a test request ID
        show_request_review("TEST-REQ-001")
        
        # Verify request data was retrieved
        mock_database["get_request"].assert_called_with("TEST-REQ-001")
        
        # Verify budget was calculated
        mock_database["calc_budget"].assert_called()