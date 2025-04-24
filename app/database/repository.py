"""
Repository module.
Provides data access layer with common CRUD operations.
"""

import logging
from datetime import datetime
import json
from app.database.connection import DatabaseManager
from app.utils.performance import profile_database_queries

class BaseRepository:
    """
    Base repository class providing common CRUD operations.
    Implements the Repository pattern for data access abstraction.
    """
    
    def __init__(self, table_name, primary_key="id"):
        """
        Initialize the repository.
        
        Args:
            table_name: Name of the database table
            primary_key: Name of the primary key column
        """
        self.table_name = table_name
        self.primary_key = primary_key
    
    @profile_database_queries
    def find_by_id(self, id_value):
        """
        Find a record by ID.
        
        Args:
            id_value: Value of the primary key
            
        Returns:
            dict: Record or None if not found
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s"
        results = DatabaseManager.execute_query(query, (id_value,))
        
        if results and len(results) > 0:
            return results[0]
        return None
    
    @profile_database_queries
    def find_all(self, where=None, params=None, order_by=None, limit=None, offset=None):
        """
        Find all records matching criteria.
        
        Args:
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for the WHERE clause
            order_by: ORDER BY clause (without 'ORDER BY' keywords)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            list: List of records
        """
        query = f"SELECT * FROM {self.table_name}"
        
        # Build query parts
        query_parts = []
        query_params = []
        
        # Add WHERE clause
        if where:
            query_parts.append(f"WHERE {where}")
            if params:
                if isinstance(params, (list, tuple)):
                    query_params.extend(params)
                else:
                    query_params.append(params)
        
        # Add ORDER BY clause
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        
        # Add LIMIT and OFFSET
        if limit:
            query_parts.append("LIMIT %s")
            query_params.append(limit)
            
            if offset:
                query_parts.append("OFFSET %s")
                query_params.append(offset)
        
        # Combine query parts
        if query_parts:
            query += " " + " ".join(query_parts)
        
        # Execute query
        return DatabaseManager.execute_query(query, tuple(query_params) if query_params else None)
    
    @profile_database_queries
    def count(self, where=None, params=None):
        """
        Count records matching criteria.
        
        Args:
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for the WHERE clause
            
        Returns:
            int: Count of matching records
        """
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        
        if where:
            query += f" WHERE {where}"
        
        results = DatabaseManager.execute_query(query, params)
        
        if results and len(results) > 0:
            return results[0]['count']
        return 0
    
    @profile_database_queries
    def create(self, data):
        """
        Create a new record.
        
        Args:
            data: Dictionary of column/value pairs
            
        Returns:
            int: ID of the created record
        """
        # Filter out None values for auto-increment columns
        if self.primary_key in data and data[self.primary_key] is None:
            del data[self.primary_key]
        
        # Build query
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        # Extract values in the same order as columns
        values = tuple(data.values())
        
        # Execute query
        with DatabaseManager.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, values)
                conn.commit()
                
                # Get inserted ID
                last_id = cursor.lastrowid
                
                return last_id
            finally:
                cursor.close()
    
    @profile_database_queries
    def update(self, id_value, data):
        """
        Update a record.
        
        Args:
            id_value: Value of the primary key
            data: Dictionary of column/value pairs to update
            
        Returns:
            bool: Success flag
        """
        # Ensure we're not updating the primary key
        if self.primary_key in data:
            del data[self.primary_key]
        
        # Build query
        set_clause = ', '.join([f"{column} = %s" for column in data.keys()])
        
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.primary_key} = %s"
        
        # Extract values in the same order as columns, add ID value at the end
        values = tuple(list(data.values()) + [id_value])
        
        # Execute query
        with DatabaseManager.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, values)
                conn.commit()
                
                # Check if any rows were updated
                return cursor.rowcount > 0
            finally:
                cursor.close()
    
    @profile_database_queries
    def delete(self, id_value):
        """
        Delete a record.
        
        Args:
            id_value: Value of the primary key
            
        Returns:
            bool: Success flag
        """
        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = %s"
        
        # Execute query
        with DatabaseManager.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (id_value,))
                conn.commit()
                
                # Check if any rows were deleted
                return cursor.rowcount > 0
            finally:
                cursor.close()
    
    @profile_database_queries
    def execute_custom_query(self, query, params=None, fetch=True):
        """
        Execute a custom SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            Query results if fetch=True, otherwise rowcount
        """
        return DatabaseManager.execute_query(query, params, fetch=fetch)
    
    @profile_database_queries
    def bulk_create(self, data_list):
        """
        Create multiple records in one operation.
        
        Args:
            data_list: List of dictionaries with column/value pairs
            
        Returns:
            int: Number of created records
        """
        if not data_list:
            return 0
        
        # Ensure all dictionaries have the same keys
        keys = data_list[0].keys()
        
        # Filter out None values for auto-increment columns
        if self.primary_key in keys:
            for data in data_list:
                if data[self.primary_key] is None:
                    del data[self.primary_key]
            
            # Update keys
            keys = data_list[0].keys()
        
        # Build query
        columns = ', '.join(keys)
        placeholders = ', '.join(['%s'] * len(keys))
        
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        # Extract values for each record
        values = [tuple(data[key] for key in keys) for data in data_list]
        
        # Execute query
        return DatabaseManager.execute_many(query, values)
    
    @profile_database_queries
    def find_with_join(self, join_clause, select_columns="*", where=None, params=None, 
                      order_by=None, limit=None, offset=None):
        """
        Find records with a JOIN clause.
        
        Args:
            join_clause: JOIN clause (including JOIN keyword)
            select_columns: Columns to select
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for the WHERE clause
            order_by: ORDER BY clause (without 'ORDER BY' keywords)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            list: List of records
        """
        query = f"SELECT {select_columns} FROM {self.table_name} {join_clause}"
        
        # Build query parts
        query_parts = []
        query_params = []
        
        # Add WHERE clause
        if where:
            query_parts.append(f"WHERE {where}")
            if params:
                if isinstance(params, (list, tuple)):
                    query_params.extend(params)
                else:
                    query_params.append(params)
        
        # Add ORDER BY clause
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        
        # Add LIMIT and OFFSET
        if limit:
            query_parts.append("LIMIT %s")
            query_params.append(limit)
            
            if offset:
                query_parts.append("OFFSET %s")
                query_params.append(offset)
        
        # Combine query parts
        if query_parts:
            query += " " + " ".join(query_parts)
        
        # Execute query
        return DatabaseManager.execute_query(query, tuple(query_params) if query_params else None)


class RequestRepository(BaseRepository):
    """Repository for travel requests."""
    
    def __init__(self):
        super().__init__("requests", "request_id")
    
    def find_requests_by_user(self, user_id, status=None):
        """
        Find requests for a specific user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            list: List of requests
        """
        where = "user_id = %s"
        params = [user_id]
        
        if status:
            where += " AND status = %s"
            params.append(status)
        
        return self.find_all(where=where, params=params, order_by="date_created DESC")
    
    def find_requests_with_user_details(self, status=None, department=None, limit=100):
        """
        Find requests with user details.
        
        Args:
            status: Optional status filter
            department: Optional department filter
            limit: Maximum number of requests to return
            
        Returns:
            list: List of requests with user details
        """
        join_clause = "JOIN users ON requests.user_id = users.user_id"
        select_columns = "requests.*, users.name, users.department"
        
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("requests.status = %s")
            params.append(status)
        
        if department:
            where_clauses.append("users.department = %s")
            params.append(department)
        
        where = " AND ".join(where_clauses) if where_clauses else None
        
        return self.find_with_join(
            join_clause=join_clause,
            select_columns=select_columns,
            where=where,
            params=params if params else None,
            order_by="requests.date_created DESC",
            limit=limit
        )
    
    def find_pending_requests_for_approval(self, approver_department=None):
        """
        Find pending requests for approval.
        
        Args:
            approver_department: Optional department filter
            
        Returns:
            list: List of pending requests
        """
        return self.find_requests_with_user_details(
            status="pending",
            department=approver_department
        )
    
    def update_request_status(self, request_id, status, notes=None, approved_by=None):
        """
        Update request status.
        
        Args:
            request_id: Request ID
            status: New status
            notes: Optional notes
            approved_by: Optional approver ID
            
        Returns:
            bool: Success flag
        """
        data = {
            "status": status,
            "date_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if notes:
            data["approval_notes"] = notes
            
        if approved_by:
            data["approved_by"] = approved_by
        
        return self.update(request_id, data)
    
    def get_request_statistics(self, department=None, year=None):
        """
        Get request statistics.
        
        Args:
            department: Optional department filter
            year: Optional year filter
            
        Returns:
            dict: Statistics
        """
        where_clauses = []
        params = []
        
        if department:
            where_clauses.append("users.department = %s")
            params.append(department)
        
        if year:
            where_clauses.append("YEAR(requests.date_from) = %s")
            params.append(year)
        
        where = " AND ".join(where_clauses) if where_clauses else None
        
        # Get status counts
        query = """
        SELECT 
            requests.status, 
            COUNT(*) as count 
        FROM 
            requests 
        JOIN 
            users ON requests.user_id = users.user_id
        """
        
        if where:
            query += f" WHERE {where}"
        
        query += " GROUP BY requests.status"
        
        results = self.execute_custom_query(query, params)
        
        # Format results
        statistics = {
            "total": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0
        }
        
        for result in results:
            status = result["status"]
            count = result["count"]
            
            statistics[status] = count
            statistics["total"] += count
        
        return statistics
    
    def get_request_with_documents(self, request_id):
        """
        Get a request with its documents.
        
        Args:
            request_id: Request ID
            
        Returns:
            dict: Request with documents
        """
        # Get request
        request = self.find_by_id(request_id)
        
        if not request:
            return None
        
        # Get documents
        document_repo = DocumentRepository()
        documents = document_repo.find_by_request(request_id)
        
        # Add documents to request
        request["documents"] = documents
        
        return request


class UserRepository(BaseRepository):
    """Repository for users."""
    
    def __init__(self):
        super().__init__("users", "user_id")
    
    def find_by_username(self, username):
        """
        Find a user by username.
        
        Args:
            username: Username
            
        Returns:
            dict: User or None if not found
        """
        results = self.find_all(where="username = %s", params=(username,))
        
        if results and len(results) > 0:
            return results[0]
        return None
    
    def authenticate(self, username, password):
        """
        Authenticate a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            dict: User if authenticated, None otherwise
        """
        # In a real application, you would hash the password
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        results = self.execute_custom_query(query, (username, password))
        
        if results and len(results) > 0:
            return results[0]
        return None
    
    def find_by_role(self, role):
        """
        Find users by role.
        
        Args:
            role: Role name
            
        Returns:
            list: List of users
        """
        return self.find_all(where="role = %s", params=(role,))
    
    def get_user_activity(self, user_id=None, days=30):
        """
        Get user activity.
        
        Args:
            user_id: Optional user ID filter
            days: Number of days to include
            
        Returns:
            list: Activity data
        """
        query = """
        SELECT 
            users.user_id,
            users.name,
            users.department,
            COUNT(requests.request_id) as request_count,
            MAX(requests.date_created) as last_activity
        FROM 
            users
        LEFT JOIN 
            requests ON users.user_id = requests.user_id
            AND requests.date_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        
        where_clauses = []
        params = [days]
        
        if user_id:
            where_clauses.append("users.user_id = %s")
            params.append(user_id)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " GROUP BY users.user_id, users.name, users.department"
        query += " ORDER BY request_count DESC, last_activity DESC"
        
        return self.execute_custom_query(query, params)


class BudgetRepository(BaseRepository):
    """Repository for budget data."""
    
    def __init__(self):
        super().__init__("budget", "budget_id")
    
    def get_current_budget(self, department=None):
        """
        Get current budget.
        
        Args:
            department: Optional department filter
            
        Returns:
            dict: Budget information
        """
        where = None
        params = None
        
        if department:
            where = "department = %s"
            params = (department,)
        
        results = self.find_all(where=where, params=params, order_by="year DESC, quarter DESC", limit=1)
        
        if results and len(results) > 0:
            return results[0]
        
        # Return default if no budget found
        return {
            "budget_id": None,
            "department": department,
            "year": datetime.now().year,
            "quarter": (datetime.now().month - 1) // 3 + 1,
            "amount": 0,
            "remaining": 0
        }
    
    def get_budget_history(self, department=None, years=1):
        """
        Get budget history.
        
        Args:
            department: Optional department filter
            years: Number of years to include
            
        Returns:
            list: Budget history
        """
        query = """
        SELECT 
            b.*,
            COALESCE(SUM(r.total_cost), 0) as spent
        FROM 
            budget b
        LEFT JOIN 
            requests r ON b.department = r.department
            AND r.status = 'approved'
            AND CONCAT(b.year, '-', b.quarter) = CONCAT(YEAR(r.date_approved), '-', QUARTER(r.date_approved))
        WHERE 
            b.year >= YEAR(DATE_SUB(NOW(), INTERVAL %s YEAR))
        """
        
        params = [years]
        
        if department:
            query += " AND b.department = %s"
            params.append(department)
        
        query += " GROUP BY b.budget_id, b.department, b.year, b.quarter"
        query += " ORDER BY b.year DESC, b.quarter DESC"
        
        return self.execute_custom_query(query, params)
    
    def get_department_spending(self, year=None):
        """
        Get spending by department.
        
        Args:
            year: Optional year filter
            
        Returns:
            list: Department spending data
        """
        query = """
        SELECT 
            requests.department,
            SUM(requests.total_cost) as total_spent,
            COUNT(requests.request_id) as request_count,
            MAX(budget.amount) as budget_amount
        FROM 
            requests
        LEFT JOIN 
            budget ON requests.department = budget.department
            AND YEAR(requests.date_approved) = budget.year
        WHERE 
            requests.status = 'approved'
        """
        
        params = []
        
        if year:
            query += " AND YEAR(requests.date_approved) = %s"
            params.append(year)
        
        query += " GROUP BY requests.department"
        query += " ORDER BY total_spent DESC"
        
        return self.execute_custom_query(query, params)


class DocumentRepository(BaseRepository):
    """Repository for documents."""
    
    def __init__(self):
        super().__init__("documents", "document_id")
    
    def find_by_request(self, request_id):
        """
        Find documents for a request.
        
        Args:
            request_id: Request ID
            
        Returns:
            list: List of documents
        """
        return self.find_all(where="request_id = %s", params=(request_id,))
    
    def add_document(self, request_id, file_name, file_type, file_content, description=None):
        """
        Add a document.
        
        Args:
            request_id: Request ID
            file_name: File name
            file_type: File type
            file_content: File content
            description: Optional description
            
        Returns:
            int: Document ID
        """
        data = {
            "request_id": request_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_content": file_content,
            "description": description,
            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return self.create(data)
    
    def get_document_content(self, document_id):
        """
        Get document content.
        
        Args:
            document_id: Document ID
            
        Returns:
            bytes: Document content
        """
        query = "SELECT file_content, file_name, file_type FROM documents WHERE document_id = %s"
        results = self.execute_custom_query(query, (document_id,))
        
        if results and len(results) > 0:
            return results[0]
        return None