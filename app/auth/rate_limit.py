"""
Rate limiting module.
Provides protection against brute force attacks.
"""

import time
import streamlit as st
from datetime import datetime, timedelta
import logging

class RateLimiter:
    """Rate limiter for protecting against brute force attacks."""
    
    def __init__(self, max_attempts=5, window_seconds=300):
        """
        Initialize rate limiter.
        
        Args:
            max_attempts: Maximum allowed attempts within the time window
            window_seconds: Time window in seconds
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._init_state()
    
    def _init_state(self):
        """Initialize state if needed."""
        if "rate_limit_attempts" not in st.session_state:
            st.session_state.rate_limit_attempts = {}
        if "rate_limit_blocks" not in st.session_state:
            st.session_state.rate_limit_blocks = {}
    
    def is_blocked(self, key):
        """
        Check if a key is currently blocked.
        
        Args:
            key: Identifier for the rate limit (e.g., IP address, user ID)
            
        Returns:
            tuple: (is_blocked, seconds_remaining)
        """
        blocks = st.session_state.rate_limit_blocks
        
        if key in blocks:
            block_until = blocks[key]
            if datetime.now() < block_until:
                # Still blocked
                seconds_left = (block_until - datetime.now()).total_seconds()
                return True, int(seconds_left)
            else:
                # Block expired
                del blocks[key]
                return False, 0
        
        return False, 0
    
    def record_attempt(self, key, success=False):
        """
        Record an authentication attempt.
        
        Args:
            key: Identifier for the rate limit
            success: Whether the attempt was successful
            
        Returns:
            tuple: (is_blocked, attempts_left)
        """
        attempts = st.session_state.rate_limit_attempts
        
        # If successful, clear previous failed attempts
        if success:
            if key in attempts:
                del attempts[key]
            return False, self.max_attempts
        
        # Initialize attempt record if needed
        if key not in attempts:
            attempts[key] = []
        
        # Clean old attempts outside the window
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        attempts[key] = [t for t in attempts[key] if t > window_start]
        
        # Record this attempt
        attempts[key].append(now)
        
        # Check if we need to block
        if len(attempts[key]) >= self.max_attempts:
            # Set block for 15 minutes
            block_until = now + timedelta(minutes=15)
            st.session_state.rate_limit_blocks[key] = block_until
            
            # Log the block
            logging.warning(f"Rate limit exceeded for {key}. Blocked until {block_until}")
            
            # Clear attempts since we're now blocking
            attempts[key] = []
            
            return True, 0
        
        return False, self.max_attempts - len(attempts[key])

# Create a global rate limiter instance
login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300)