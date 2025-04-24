"""
Database connection module.
Provides database connection management.
"""

import mysql.connector
from mysql.connector import pooling
import logging
import os
from contextlib import contextmanager
from app.utils.performance import profile_database_queries

class DatabaseManager:
    """Database connection manager for FTCS."""
    
    _connection_pool = None
    
    @classmethod
    def initialize_pool(cls):
        """Initialize the database connection pool."""
        try:
            if cls._connection_pool is None:
                # Get database configuration from environment
                db_config = {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'user': os.getenv('DB_USER', 'root'),
                    'password': os.getenv('DB_PASSWORD', ''),
                    'database': os.getenv('DB_NAME', 'con_system'),
                    'pool_name': 'ftcs_pool',
                    'pool_size': 10,
                    'pool_reset_session': True
                }
                
                cls._connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
                logging.info("Database connection pool initialized")
        except Exception as e:
            logging.error(f"Error initializing database connection pool: {e}")
            raise
    
    @classmethod
    def get_connection(cls):
        """Get a connection from the pool."""
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.get_connection()
    
    @classmethod
    @contextmanager
    def connection(cls):
        """Context manager for database connections."""
        conn = None
        try:
            conn = cls.get_connection()
            yield conn
        finally:
            if conn:
                conn.close()
    
    @classmethod
    @profile_database_queries  # Add performance profiling to all database queries
    def execute_query(cls, query, params=None, fetch=True, commit=False):
        """
        Execute a database query with profiling.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple, list of tuples, or dict)
            fetch: Whether to fetch results
            commit: Whether to commit the transaction
            
        Returns:
            Query results if fetch=True, otherwise None
        """
        with cls.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params)
                
                if commit:
                    conn.commit()
                
                if fetch:
                    results = cursor.fetchall()
                    return results
                    
                return None
                
            except Exception as e:
                if commit:
                    conn.rollback()
                logging.error(f"Database error: {e}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    @profile_database_queries
    def execute_many(cls, query, params_list):
        """
        Execute a batch operation with profiling.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of rows affected
        """
        with cls.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                logging.error(f"Database batch error: {e}")
                raise
            finally:
                cursor.close()