"""
Configuration module for the Conference Travel System.
Handles loading environment variables and application settings.
"""

import os
from dotenv import load_dotenv
import logging

# Load environment variables
def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    logging.info("Environment variables loaded")

# Move database config to environment variables
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),  # Will be replaced by env var
    "database": os.getenv("DB_NAME", "con_system"),
    "pool_name": "con_system_pool",
    "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
}

# Application constants
PURPOSE_OPTIONS = ["Attending a Conference", "Presenting at a Conference"]
INDEX_OPTIONS = ["Scopus", "IEEE", "Web of Science", "PubMed", "MEDLINE", "ACM", "None"]
LOCATION_OPTIONS = {
    "USA": ["New York", "Los Angeles", "Chicago"],
    "Canada": ["Toronto", "Vancouver", "Montreal"],
    "Germany": ["Berlin", "Munich", "Hamburg"],
}

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30

# Maximum login attempts before lockout
MAX_LOGIN_ATTEMPTS = 5

# Lockout duration in minutes
LOCKOUT_DURATION_MINUTES = 15