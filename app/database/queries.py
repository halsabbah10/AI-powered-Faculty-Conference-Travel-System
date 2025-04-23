"""
Database queries module.
Contains functions for database operations organized by entity.
"""

import logging
import json
from datetime import datetime
from app.database.connection import DatabaseManager
import streamlit as st

#############################################
# User & Authentication Related Queries
#############################################

def get_user_by_id(user_id):
    """Get user details by user ID"""
    try:
        query = "SELECT * FROM faculty WHERE user_id = %s"
        result = DatabaseManager.execute_query(query, (user_id,))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Error in get_user_by_id: {str(e)}")
        return None

def log_user_activity(user_id, activity_type, details=None, ip_address="127.0.0.1"):
    """Log user activity for audit purposes"""
    try:
        details_json = json.dumps(details) if details else "{}"
        
        query = """
        INSERT INTO user_activity_log 
        (user_id, activity_type, details, ip_address, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        DatabaseManager.execute_query(
            query, 
            (user_id, activity_type, details_json, ip_address),
            fetch=False,
            commit=True
        )
        return True
    except Exception as e:
        logging.error(f"Error in log_user_activity: {str(e)}")
        return False

#############################################
# Request Related Queries
#############################################

def get_user_requests(user_id, status=None, limit=50):
    """Get requests submitted by a specific user"""
    try:
        if status:
            query = """
            SELECT * FROM requests 
            WHERE faculty_user_id = %s AND status = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            params = (user_id, status, limit)
        else:
            query = """
            SELECT * FROM requests 
            WHERE faculty_user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            params = (user_id, limit)
            
        return DatabaseManager.execute_query(query, params)
    except Exception as e:
        logging.error(f"Error in get_user_requests: {str(e)}")
        return []

def get_request_by_id(request_id):
    """Get a specific request by ID"""
    try:
        query = """
        SELECT r.*, f.name as faculty_name, f.department
        FROM requests r
        JOIN faculty f ON r.faculty_user_id = f.user_id
        WHERE r.request_id = %s
        """
        result = DatabaseManager.execute_query(query, (request_id,))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Error in get_request_by_id: {str(e)}")
        return None

def create_request(faculty_user_id, request_data):
    """Create a new conference travel request"""
    try:
        query = """
        INSERT INTO requests (
            request_id, faculty_user_id, conference_name, purpose_of_attending,
            conference_url, url_summary, destination, city, date_from, date_to,
            per_diem, registration_fee, visa_fee, conference_summary,
            research_summary, notes_summary, index_type, created_at, status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'pending'
        )
        """
        
        # Generate unique request ID
        import uuid
        request_id = str(uuid.uuid4())
        
        params = (
            request_id,
            faculty_user_id,
            request_data.get('conference_name'),
            request_data.get('purpose_of_attending'),
            request_data.get('conference_url'),
            request_data.get('url_summary'),
            request_data.get('destination'),
            request_data.get('city'),
            request_data.get('date_from'),
            request_data.get('date_to'),
            request_data.get('per_diem'),
            request_data.get('registration_fee'),
            request_data.get('visa_fee'),
            request_data.get('conference_summary'),
            request_data.get('research_summary'),
            request_data.get('notes_summary'),
            request_data.get('index_type')
        )
        
        DatabaseManager.execute_query(query, params, fetch=False, commit=True)
        return request_id
    except Exception as e:
        logging.error(f"Error in create_request: {str(e)}")
        return None

def update_request_status(request_id, status, reviewer_id=None, comments=None):
    """Update request status and add reviewer comments if provided"""
    try:
        if reviewer_id and comments:
            query = """
            UPDATE requests 
            SET status = %s, reviewer_id = %s, review_comments = %s, reviewed_at = NOW()
            WHERE request_id = %s
            """
            params = (status, reviewer_id, comments, request_id)
        else:
            query = """
            UPDATE requests 
            SET status = %s
            WHERE request_id = %s
            """
            params = (status, request_id)
            
        DatabaseManager.execute_query(query, params, fetch=False, commit=True)
        return True
    except Exception as e:
        logging.error(f"Error in update_request_status: {str(e)}")
        return False

def get_pending_requests(limit=50):
    """Get all pending requests for approval"""
    try:
        query = """
        SELECT r.*, f.name as faculty_name, f.department
        FROM requests r
        JOIN faculty f ON r.faculty_user_id = f.user_id
        WHERE r.status = 'pending'
        ORDER BY r.created_at
        LIMIT %s
        """
        
        return DatabaseManager.execute_query(query, (limit,))
    except Exception as e:
        logging.error(f"Error in get_pending_requests: {str(e)}")
        return []

def search_requests(search_term, status=None, limit=50):
    """Search requests by conference name, faculty name, or destination"""
    try:
        search_param = f"%{search_term}%"
        
        if status:
            query = """
            SELECT r.*, f.name as faculty_name, f.department
            FROM requests r
            JOIN faculty f ON r.faculty_user_id = f.user_id
            WHERE r.status = %s AND (
                r.conference_name LIKE %s OR
                f.name LIKE %s OR
                r.destination LIKE %s OR
                r.city LIKE %s
            )
            ORDER BY r.created_at DESC
            LIMIT %s
            """
            params = (status, search_param, search_param, search_param, search_param, limit)
        else:
            query = """
            SELECT r.*, f.name as faculty_name, f.department
            FROM requests r
            JOIN faculty f ON r.faculty_user_id = f.user_id
            WHERE 
                r.conference_name LIKE %s OR
                f.name LIKE %s OR
                r.destination LIKE %s OR
                r.city LIKE %s
            ORDER BY r.created_at DESC
            LIMIT %s
            """
            params = (search_param, search_param, search_param, search_param, limit)
            
        return DatabaseManager.execute_query(query, params)
    except Exception as e:
        logging.error(f"Error in search_requests: {str(e)}")
        return []

#############################################
# Budget Related Queries
#############################################

def get_budget_info():
    """Get current budget information"""
    try:
        query = "SELECT * FROM budget ORDER BY year DESC, period DESC LIMIT 1"
        result = DatabaseManager.execute_query(query)
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Error in get_budget_info: {str(e)}")
        return None

def update_budget(year, period, amount, modified_by):
    """Update budget for a specific year and period"""
    try:
        # First, check if budget entry exists
        check_query = "SELECT * FROM budget WHERE year = %s AND period = %s"
        existing = DatabaseManager.execute_query(check_query, (year, period))
        
        if existing:
            # Update existing budget
            query = """
            UPDATE budget 
            SET amount = %s, modified_by = %s, modified_at = NOW()
            WHERE year = %s AND period = %s
            """
            params = (amount, modified_by, year, period)
        else:
            # Create new budget entry
            query = """
            INSERT INTO budget (year, period, amount, modified_by, modified_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            params = (year, period, amount, modified_by)
            
        DatabaseManager.execute_query(query, params, fetch=False, commit=True)
        
        # Record in budget history
        history_query = """
        INSERT INTO budgethistory (year, period, amount, modified_by, modified_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        DatabaseManager.execute_query(history_query, params, fetch=False, commit=True)
        
        return True
    except Exception as e:
        logging.error(f"Error in update_budget: {str(e)}")
        return False

def get_budget_history(limit=20):
    """Get budget adjustment history"""
    try:
        query = """
        SELECT bh.*, f.name as modifier_name
        FROM budgethistory bh
        JOIN faculty f ON bh.modified_by = f.user_id
        ORDER BY bh.modified_at DESC
        LIMIT %s
        """
        
        return DatabaseManager.execute_query(query, (limit,))
    except Exception as e:
        logging.error(f"Error in get_budget_history: {str(e)}")
        return []

def calculate_remaining_budget():
    """Calculate remaining budget based on approved requests"""
    try:
        # Get current budget
        budget_info = get_budget_info()
        if not budget_info:
            return 0, 0, 0
            
        total_budget = budget_info['amount']
        
        # Calculate total approved expenses for current period
        expense_query = """
        SELECT SUM(per_diem + registration_fee + visa_fee) as total_expense
        FROM requests
        WHERE status = 'approved' 
        AND YEAR(created_at) = %s
        """
        
        current_year = datetime.now().year
        expenses = DatabaseManager.execute_query(expense_query, (current_year,))
        
        total_expenses = expenses[0]['total_expense'] if expenses and expenses[0]['total_expense'] else 0
        remaining_budget = total_budget - total_expenses
        
        return total_budget, total_expenses, remaining_budget
    except Exception as e:
        logging.error(f"Error in calculate_remaining_budget: {str(e)}")
        return 0, 0, 0

#############################################
# Analytics & Reporting Queries
#############################################

def get_requests_by_status():
    """Get count of requests by status for current year"""
    try:
        query = """
        SELECT status, COUNT(*) as count
        FROM requests
        WHERE YEAR(created_at) = YEAR(CURDATE())
        GROUP BY status
        """
        
        return DatabaseManager.execute_query(query)
    except Exception as e:
        logging.error(f"Error in get_requests_by_status: {str(e)}")
        return []

def get_requests_by_month(year=None):
    """Get monthly request counts for a specific year"""
    try:
        if not year:
            year = datetime.now().year
            
        query = """
        SELECT MONTH(created_at) as month, COUNT(*) as count
        FROM requests
        WHERE YEAR(created_at) = %s
        GROUP BY MONTH(created_at)
        ORDER BY month
        """
        
        return DatabaseManager.execute_query(query, (year,))
    except Exception as e:
        logging.error(f"Error in get_requests_by_month: {str(e)}")
        return []

def get_top_destinations(limit=5):
    """Get most popular travel destinations"""
    try:
        query = """
        SELECT destination, COUNT(*) as count
        FROM requests
        WHERE status IN ('approved', 'pending', 'completed')
        GROUP BY destination
        ORDER BY count DESC
        LIMIT %s
        """
        
        return DatabaseManager.execute_query(query, (limit,))
    except Exception as e:
        logging.error(f"Error in get_top_destinations: {str(e)}")
        return []

def get_faculty_travel_frequency(limit=10):
    """Get faculty members by travel frequency"""
    try:
        query = """
        SELECT f.name, COUNT(r.request_id) as request_count
        FROM faculty f
        LEFT JOIN requests r ON f.user_id = r.faculty_user_id
        WHERE f.role = 'professor'
        GROUP BY f.user_id
        ORDER BY request_count DESC
        LIMIT %s
        """
        
        return DatabaseManager.execute_query(query, (limit,))
    except Exception as e:
        logging.error(f"Error in get_faculty_travel_frequency: {str(e)}")
        return []

def get_department_spending():
    """Get total spending by department"""
    try:
        query = """
        SELECT f.department, 
               SUM(r.per_diem + r.registration_fee + r.visa_fee) as total_expense
        FROM requests r
        JOIN faculty f ON r.faculty_user_id = f.user_id
        WHERE r.status = 'approved' OR r.status = 'completed'
        GROUP BY f.department
        ORDER BY total_expense DESC
        """
        
        return DatabaseManager.execute_query(query)
    except Exception as e:
        logging.error(f"Error in get_department_spending: {str(e)}")
        return []

#############################################
# Document Related Queries
#############################################

def save_document(request_id, file_name, file_type, file_data, file_size):
    """Save uploaded document to the database"""
    try:
        query = """
        INSERT INTO uploadedfiles 
        (request_id, file_name, file_type, file_data, file_size, upload_date)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        
        params = (request_id, file_name, file_type, file_data, file_size)
        
        DatabaseManager.execute_query(query, params, fetch=False, commit=True)
        return True
    except Exception as e:
        logging.error(f"Error in save_document: {str(e)}")
        return False

def get_document(request_id, file_type):
    """Retrieve a document by request ID and file type"""
    try:
        query = """
        SELECT * FROM uploadedfiles
        WHERE request_id = %s AND file_type = %s
        """
        
        result = DatabaseManager.execute_query(query, (request_id, file_type))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Error in get_document: {str(e)}")
        return None