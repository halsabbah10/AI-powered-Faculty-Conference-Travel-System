"""
Database connection module.
Manages database connections and provides a connection pool.
"""

import os
import logging
import mysql.connector
import mysql.connector.pooling
from contextlib import contextmanager

# Load environment variables for database configuration
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "con_system"),
    "pool_name": "con_system_pool",
    "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
}

# Initialize connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
    logging.info("Database connection pool created successfully")
except Exception as e:
    logging.error(f"Error creating connection pool: {str(e)}")
    connection_pool = None

@contextmanager
def get_db_connection():
    """
    Get a connection from the pool as a context manager.
    Usage:
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
    """
    conn = None
    try:
        conn = connection_pool.get_connection() if connection_pool else None
        if not conn:
            # Fallback to direct connection if pool isn't available
            conn = mysql.connector.connect(
                host=db_config["host"],
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"]
            )
        yield conn
    except mysql.connector.Error as e:
        logging.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def execute_query(query, params=None, fetch=True, commit=False, dictionary=True):
    """
    Execute a database query with proper error handling.
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
        fetch (bool): Whether to fetch results
        commit (bool): Whether to commit the transaction
        dictionary (bool): Whether to return results as dictionaries
        
    Returns:
        list: Query results (if fetch=True)
        int: Last row ID (if commit=True and an INSERT was performed)
        None: If no results to return
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(query, params or ())
            result = None
            
            if fetch:
                result = cursor.fetchall()
            elif commit:
                conn.commit()
                if cursor.lastrowid:
                    result = cursor.lastrowid
            
            return result
        except mysql.connector.Error as e:
            if commit:
                conn.rollback()
            logging.error(f"Query error: {str(e)}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            raise
        finally:
            cursor.close()

# Simplified interface for common database operations
def query_one(query, params=None):
    """Execute query and return the first result"""
    results = execute_query(query, params, fetch=True)
    return results[0] if results else None

def query_all(query, params=None):
    """Execute query and return all results"""
    return execute_query(query, params, fetch=True)

def execute(query, params=None):
    """Execute query without returning results"""
    return execute_query(query, params, fetch=False, commit=True)

def insert(query, params=None):
    """Execute insert query and return the last insert ID"""
    return execute_query(query, params, fetch=False, commit=True)