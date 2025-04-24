"""
Advanced caching module.
Provides sophisticated caching strategies for the application.
"""

import functools
import logging
import time
import hashlib
import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st

# Cache directory
CACHE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Memory cache storage
_memory_cache = {}

def timed_lru_cache(maxsize=128, ttl_seconds=3600):
    """
    Decorator combining LRU cache with time-based expiration.
    
    Args:
        maxsize: Maximum cache size
        ttl_seconds: Time to live in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Create cache
        cache = {}
        # Track access timestamps and order
        timestamps = {}
        call_order = []
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create key
            key = _create_cache_key(func.__name__, args, kwargs)
            
            # Check if key in cache and not expired
            current_time = time.time()
            if key in cache:
                timestamp = timestamps.get(key, 0)
                if current_time - timestamp <= ttl_seconds:
                    # Update access order
                    if key in call_order:
                        call_order.remove(key)
                    call_order.append(key)
                    return cache[key]
                else:
                    # Expired, remove from cache
                    del cache[key]
                    if key in timestamps:
                        del timestamps[key]
                    if key in call_order:
                        call_order.remove(key)
            
            # Calculate new value
            result = func(*args, **kwargs)
            
            # Add to cache
            cache[key] = result
            timestamps[key] = current_time
            call_order.append(key)
            
            # Ensure cache size
            if maxsize > 0 and len(cache) > maxsize:
                # Remove oldest entry
                oldest_key = call_order.pop(0)
                if oldest_key in cache:
                    del cache[oldest_key]
                if oldest_key in timestamps:
                    del timestamps[oldest_key]
            
            return result
        
        # Add clear method
        def clear_cache():
            cache.clear()
            timestamps.clear()
            call_order.clear()
        
        wrapper.clear_cache = clear_cache
        
        return wrapper
    
    return decorator

def persistent_cache(ttl_seconds=86400, subdir=None):
    """
    Decorator for persistent caching to disk.
    
    Args:
        ttl_seconds: Time to live in seconds
        subdir: Optional subdirectory for cache files
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Create subdirectory if specified
        cache_path = CACHE_DIR
        if subdir:
            cache_path = cache_path / subdir
            cache_path.mkdir(exist_ok=True)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = _create_cache_key(func.__name__, args, kwargs)
            
            # Add hash to make filename safe
            filename = f"{func.__name__}_{hashlib.md5(key.encode()).hexdigest()}.cache"
            file_path = cache_path / filename
            
            # Check if file exists and not expired
            if file_path.exists():
                # Check file age
                file_time = os.path.getmtime(file_path)
                current_time = time.time()
                
                if current_time - file_time <= ttl_seconds:
                    try:
                        with open(file_path, 'rb') as f:
                            return pickle.load(f)
                    except Exception as e:
                        logging.warning(f"Error loading cache file: {str(e)}")
            
            # Calculate new value
            result = func(*args, **kwargs)
            
            # Save to cache
            try:
                with open(file_path, 'wb') as f:
                    pickle.dump(result, f)
            except Exception as e:
                logging.warning(f"Error saving cache file: {str(e)}")
            
            return result
        
        # Add clear method
        def clear_cache():
            for f in cache_path.glob(f"{func.__name__}_*.cache"):
                try:
                    os.remove(f)
                except:
                    pass
        
        wrapper.clear_cache = clear_cache
        
        return wrapper
    
    return decorator

def streamlit_cache(ttl_hours=24):
    """
    Decorator for Streamlit's built-in caching.
    
    Args:
        ttl_hours: Time to live in hours
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Create cached function
        cached_func = st.cache_data(ttl=timedelta(hours=ttl_hours))(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return cached_func(*args, **kwargs)
        
        # Add clear method that calls Streamlit's clear
        wrapper.clear_cache = cached_func.clear
        
        return wrapper
    
    return decorator

def request_cache(user_specific=False):
    """
    Cache results for the current request/session.
    
    Args:
        user_specific: Whether cache should be specific to the current user
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create key
            base_key = _create_cache_key(func.__name__, args, kwargs)
            
            # Add user prefix if user-specific
            if user_specific and hasattr(st, "session_state") and "logged_in_user" in st.session_state:
                cache_key = f"{st.session_state.logged_in_user}:{base_key}"
            else:
                cache_key = base_key
            
            # Use Streamlit's session state for request caching
            cache_dict_key = f"_request_cache_{func.__module__}"
            
            if cache_dict_key not in st.session_state:
                st.session_state[cache_dict_key] = {}
            
            # Check if result is cached
            if cache_key in st.session_state[cache_dict_key]:
                return st.session_state[cache_dict_key][cache_key]
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Store in cache
            st.session_state[cache_dict_key][cache_key] = result
            
            return result
        
        # Add clear method
        def clear_cache():
            cache_dict_key = f"_request_cache_{func.__module__}"
            if hasattr(st, "session_state") and cache_dict_key in st.session_state:
                st.session_state[cache_dict_key] = {}
        
        wrapper.clear_cache = clear_cache
        
        return decorator
    
    return decorator

def cache_manager_ui():
    """Admin UI for managing cache."""
    st.subheader("Cache Management")
    
    # Get cache statistics
    cache_stats = _get_cache_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Memory Cache Entries", cache_stats["memory_entries"])
    with col2:
        st.metric("Disk Cache Files", cache_stats["disk_entries"])
    with col3:
        st.metric("Disk Cache Size", f"{cache_stats['disk_size_mb']:.2f} MB")
    
    # Option to clear specific cache or all
    st.subheader("Clear Cache")
    
    clear_option = st.radio(
        "Select cache to clear:",
        ["Memory Cache", "Disk Cache", "All Cache"]
    )
    
    if st.button("Clear Selected Cache"):
        if clear_option == "Memory Cache":
            _clear_memory_cache()
            st.success("Memory cache cleared successfully!")
        elif clear_option == "Disk Cache":
            _clear_disk_cache()
            st.success("Disk cache cleared successfully!")
        else:
            _clear_memory_cache()
            _clear_disk_cache()
            st.success("All caches cleared successfully!")
        
        # Refresh stats
        st.experimental_rerun()
    
    # Show cached endpoints
    if cache_stats["disk_entries"] > 0:
        st.subheader("Cached Endpoints")
        
        # Get unique function names from cache files
        cache_files = list(CACHE_DIR.glob("**/*.cache"))
        functions = set()
        
        for file in cache_files:
            # Extract function name from filename (before the underscore)
            parts = file.name.split("_", 1)
            if parts:
                functions.add(parts[0])
        
        # Display as a table
        if functions:
            from datetime import datetime
            
            function_stats = []
            
            for func in sorted(functions):
                # Count files for this function
                files = list(CACHE_DIR.glob(f"{func}_*.cache"))
                
                if files:
                    # Get most recent file
                    newest_file = max(files, key=os.path.getmtime)
                    last_updated = datetime.fromtimestamp(os.path.getmtime(newest_file))
                    
                    # Get total size
                    total_size = sum(os.path.getsize(f) for f in files)
                    
                    function_stats.append({
                        "Function": func,
                        "Cache Entries": len(files),
                        "Last Updated": last_updated,
                        "Cache Size": f"{total_size / 1024:.2f} KB"
                    })
            
            import pandas as pd
            stats_df = pd.DataFrame(function_stats)
            st.dataframe(stats_df)

def _create_cache_key(func_name, args, kwargs):
    """Create a string key from function arguments."""
    # Convert args and kwargs to a stable string representation
    args_str = str(args)
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    return f"{func_name}:{args_str}:{kwargs_str}"

def _get_cache_stats():
    """Get statistics about the cache."""
    # Memory cache stats
    memory_entries = len(_memory_cache)
    
    # Disk cache stats
    cache_files = list(CACHE_DIR.glob("**/*.cache"))
    disk_entries = len(cache_files)
    
    # Calculate total size
    disk_size = sum(os.path.getsize(f) for f in cache_files if os.path.isfile(f))
    disk_size_mb = disk_size / (1024 * 1024)  # Convert to MB
    
    return {
        "memory_entries": memory_entries,
        "disk_entries": disk_entries,
        "disk_size_mb": disk_size_mb
    }

def _clear_memory_cache():
    """Clear all memory caches."""
    global _memory_cache
    _memory_cache = {}
    
    # Also clear any module-level caches
    for name, module in sys.modules.items():
        if hasattr(module, "_cache") and isinstance(module._cache, dict):
            module._cache.clear()

def _clear_disk_cache():
    """Clear all disk caches."""
    for cache_file in CACHE_DIR.glob("**/*.cache"):
        try:
            os.remove(cache_file)
        except:
            pass

# Example usages:

@timed_lru_cache(maxsize=100, ttl_seconds=3600)
def expensive_calculation(a, b):
    """Example function using memory cache with expiration."""
    time.sleep(2)  # Simulate expensive operation
    return a + b

@persistent_cache(ttl_seconds=86400, subdir="database")
def fetch_large_dataset(query_params):
    """Example function using persistent disk cache."""
    # This would normally be a database query
    time.sleep(3)  # Simulate database query
    return [i for i in range(1000)]

@streamlit_cache(ttl_hours=1)
def generate_chart_data(n_points):
    """Example function using Streamlit's built-in cache."""
    import pandas as pd
    import numpy as np
    
    # Create example chart data
    dates = pd.date_range(start=datetime.now() - timedelta(days=n_points), periods=n_points)
    data = np.random.randn(n_points).cumsum()
    
    return pd.DataFrame({
        'date': dates,
        'value': data
    })

@request_cache(user_specific=True)
def get_user_permissions():
    """Example function using request/session cache."""
    # This would normally check a database
    time.sleep(1)  # Simulate permission lookup
    return ["read", "write"]