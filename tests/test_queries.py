"""
Tests for database query functions.
"""

import pytest
from datetime import datetime, timedelta

from app.database.queries import (
    get_user_by_id,
    update_request_status,
    get_available_budget,
    calculate_remaining_budget
)

def test_get_user_by_id(test_db_connection):
    """Test retrieving a user by ID."""
    # Get test user
    user = get_user_by_id('test_prof')
    
    # Check user data
    assert user is not None
    assert user['user_id'] == 'test_prof'
    assert user['name'] == 'Test Professor'
    assert user['department'] == 'Computer Science'
    assert user['role'] == 'professor'

def test_update_request_status(test_db_connection):
    """Test updating a request status."""
    # Update test request
    update_request_status('TEST-REQ-001', 'approved', 'Test approval notes')
    
    # Query the database directly to verify
    from app.database.connection import DatabaseManager
    result = DatabaseManager.execute_query(
        "SELECT status, approval_notes FROM requests WHERE request_id = %s",
        ('TEST-REQ-001',)
    )
    
    # Check status update
    assert result
    assert result[0]['status'] == 'approved'
    assert result[0]['approval_notes'] == 'Test approval notes'

def test_get_available_budget(test_db_connection):
    """Test retrieving available budget."""
    # Get budget
    budget = get_available_budget()
    
    # Budget should be 50000.00 as set in test data
    assert budget == 50000.00

def test_calculate_remaining_budget(test_db_connection):
    """Test calculating remaining budget."""
    # Create an approved request with costs
    from app.database.connection import DatabaseManager
    DatabaseManager.execute_query(
        """
        INSERT INTO requests (
            request_id, faculty_user_id, conference_name, purpose_of_attending,
            conference_url, destination, city, date_from, date_to,
            per_diem, registration_fee, visa_fee, status
        )
        VALUES (
            'TEST-REQ-002', 'test_prof', 'Test Conference 2', 'Attending',
            'http://test2.com', 'Germany', 'Berlin',
            DATE_ADD(CURDATE(), INTERVAL 60 DAY), DATE_ADD(CURDATE(), INTERVAL 65 DAY),
            300.00, 700.00, 100.00, 'approved'
        )
        """,
        fetch=False,
        commit=True
    )
    
    # Calculate remaining budget
    total, spent, remaining = calculate_remaining_budget()
    
    # Check calculations
    assert total == 50000.00
    assert spent == 1100.00  # 300 + 700 + 100
    assert remaining == 48900.00  # 50000 - 1100