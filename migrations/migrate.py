"""
Database migration script.
Handles version control for database schema.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import mysql.connector
import re

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import application modules
from app.config import load_environment
from app.database.connection import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory for migration files
MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))

def get_current_version():
    """
    Get current database schema version.
    
    Returns:
        int: Current schema version
    """
    try:
        # Check if version table exists
        check_query = """
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = 'schema_version'
        """
        
        result = DatabaseManager.execute_query(check_query)
        
        if result[0]['count'] == 0:
            # Create version table
            create_query = """
            CREATE TABLE schema_version (
                id INT AUTO_INCREMENT PRIMARY KEY,
                version INT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description VARCHAR(255)
            )
            """
            
            DatabaseManager.execute_query(create_query, fetch=False, commit=True)
            
            # Insert initial version
            insert_query = """
            INSERT INTO schema_version (version, description)
            VALUES (0, 'Initial schema')
            """
            
            DatabaseManager.execute_query(insert_query, fetch=False, commit=True)
            
            return 0
        
        # Get current version
        version_query = """
        SELECT version
        FROM schema_version
        ORDER BY version DESC
        LIMIT 1
        """
        
        result = DatabaseManager.execute_query(version_query)
        
        if result:
            return result[0]['version']
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error getting schema version: {str(e)}")
        return 0

def update_version(version, description):
    """
    Update schema version in database.
    
    Args:
        version: New schema version
        description: Description of the migration
        
    Returns:
        bool: Success status
    """
    try:
        query = """
        INSERT INTO schema_version (version, description)
        VALUES (%s, %s)
        """
        
        DatabaseManager.execute_query(
            query, 
            (version, description),
            fetch=False,
            commit=True
        )
        
        logger.info(f"Updated schema version to {version}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating schema version: {str(e)}")
        return False

def get_migration_files():
    """
    Get all migration SQL files sorted by version.
    
    Returns:
        list: Sorted migration files
    """
    files = []
    
    # Pattern to match migration files: V{version}__description.sql
    pattern = r"^V(\d+)__(.+)\.sql$"
    
    for filename in os.listdir(MIGRATIONS_DIR):
        match = re.match(pattern, filename)
        if match:
            version = int(match.group(1))
            description = match.group(2).replace('_', ' ')
            files.append({
                "version": version,
                "description": description,
                "filename": filename
            })
    
    # Sort by version
    return sorted(files, key=lambda x: x["version"])

def run_migration(file_info):
    """
    Run a single migration file.
    
    Args:
        file_info: Dictionary with migration file details
        
    Returns:
        bool: Success status
    """
    try:
        # Read SQL file
        file_path = os.path.join(MIGRATIONS_DIR, file_info["filename"])
        with open(file_path, 'r') as f:
            sql = f.read()
        
        # Split into statements
        statements = sql.split(';')
        
        # Execute each statement
        conn = None
        cursor = None
        
        try:
            # Get a connection
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            # Update version
            cursor.execute(
                "INSERT INTO schema_version (version, description) VALUES (%s, %s)",
                (file_info["version"], file_info["description"])
            )
            
            # Commit transaction
            conn.commit()
            
            logger.info(f"Successfully applied migration V{file_info['version']}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"Error applying migration V{file_info['version']}: {str(e)}")
        return False

def create_migration(description):
    """
    Create a new migration file.
    
    Args:
        description: Description of the migration
        
    Returns:
        str: Path to the created file
    """
    try:
        # Get all migrations
        migrations = get_migration_files()
        
        # Determine new version
        new_version = 1
        if migrations:
            new_version = migrations[-1]["version"] + 1
        
        # Format description for filename
        filename_desc = description.lower().replace(' ', '_')
        
        # Create filename
        filename = f"V{new_version}__{filename_desc}.sql"
        file_path = os.path.join(MIGRATIONS_DIR, filename)
        
        # Create file
        with open(file_path, 'w') as f:
            f.write(f"-- Migration: {description}\n")
            f.write(f"-- Version: {new_version}\n")
            f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("-- Add your SQL statements here\n")
        
        logger.info(f"Created new migration file: {filename}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error creating migration: {str(e)}")
        return None

def main():
    """Main entry point for migration tool."""
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run pending migrations")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("description", help="Description of the migration")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_environment()
    
    # Process commands
    if args.command == "status":
        # Show migration status
        current_version = get_current_version()
        migrations = get_migration_files()
        
        print(f"Current database version: {current_version}")
        print("\nAvailable migrations:")
        
        for migration in migrations:
            status = "Applied" if migration["version"] <= current_version else "Pending"
            print(f"V{migration['version']}: {migration['description']} [{status}]")
            
    elif args.command == "migrate":
        # Run migrations
        current_version = get_current_version()
        migrations = get_migration_files()
        
        pending = [m for m in migrations if m["version"] > current_version]
        
        if not pending:
            print("Database is up to date. No migrations to apply.")
            return
        
        print(f"Current version: {current_version}")
        print(f"Found {len(pending)} pending migrations")
        
        for migration in pending:
            print(f"Applying V{migration['version']}: {migration['description']}...")
            success = run_migration(migration)
            
            if not success:
                print(f"Migration failed. Stopping at version {current_version}")
                return
        
        new_version = pending[-1]["version"]
        print(f"Successfully migrated to version {new_version}")
        
    elif args.command == "create":
        # Create new migration
        file_path = create_migration(args.description)
        if file_path:
            print(f"Created new migration file: {file_path}")
            print("Edit this file to add your SQL statements.")
        else:
            print("Failed to create migration file.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()