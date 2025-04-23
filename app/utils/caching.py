"""
Caching utilities to improve performance.
"""

import functools
import hashlib
import pickle
import time
import logging
import streamlit as st
from datetime import datetime, timedelta

def timed_lru_cache(seconds=600, maxsize=128):
    """
    Decorator that caches a function's return value with an expiration time.
    
    Args:
        seconds: Time to live for cached values (default 10 minutes)
        maxsize: Maximum cache size (number of items)
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        # Use functools LRU cache
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs), time.time()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result, timestamp = cached_func(*args, **kwargs)
            
            # Check if result is expired
            if time.time() - timestamp > seconds:
                # Clear this item from cache
                cached_func.cache_clear()
                # Get fresh result
                result, _ = cached_func(*args, **kwargs)
            
            return result
            
        return wrapper
    
    return decorator

class SessionCache:
    """Cache that stores values in Streamlit session state."""
    
    @staticmethod
    def _get_cache_dict():
        """Get or initialize the cache dictionary in session state."""
        if "app_cache" not in st.session_state:
            st.session_state.app_cache = {}
        return st.session_state.app_cache
    
    @staticmethod
    def get(key, default=None, ttl_seconds=None):
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            ttl_seconds: Time-to-live in seconds (optional)
            
        Returns:
            Cached value or default
        """
        cache = SessionCache._get_cache_dict()
        
        if key not in cache:
            return default
            
        value, timestamp = cache[key]
        
        # Check expiration if TTL provided
        if ttl_seconds is not None:
            if time.time() - timestamp > ttl_seconds:
                # Expired
                del cache[key]
                return default
                
        return value
    
    @staticmethod
    def set(key, value, ttl_seconds=None):
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time-to-live in seconds (optional)
            
        Returns:
            The stored value
        """
        cache = SessionCache._get_cache_dict()
        cache[key] = (value, time.time())
        return value
    
    @staticmethod
    def delete(key):
        """Delete a value from the cache."""
        cache = SessionCache._get_cache_dict()
        if key in cache:
            del cache[key]
    
    @staticmethod
    def clear():
        """Clear all cached values."""
        st.session_state.app_cache = {}

def cache_expensive_operation(key=None, ttl_seconds=600):
    """
    Decorator for caching expensive operations in session state.
    
    Args:
        key: Optional function-specific key prefix
        ttl_seconds: Time-to-live in seconds
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key:
                cache_key = f"{key}:"
            else:
                cache_key = f"{func.__module__}.{func.__name__}:"
            
            # Add arguments to key
            arg_key = hashlib.md5(
                pickle.dumps((args, frozenset(kwargs.items())))
            ).hexdigest()
            cache_key += arg_key
            
            # Try to get from cache
            cached_value = SessionCache.get(
                cache_key, 
                default=None,
                ttl_seconds=ttl_seconds
            )
            
            if cached_value is not None:
                return cached_value
            
            # Not in cache, call function
            result = func(*args, **kwargs)
            
            # Store in cache
            SessionCache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator