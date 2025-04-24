"""
Performance monitoring module.
Provides timing and profiling utilities.
"""

import time
import inspect
import functools
import logging
import threading
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Global storage for performance metrics
if "performance_metrics" not in st.session_state:
    st.session_state.performance_metrics = []

# Maximum metrics to store
MAX_METRICS = 1000

def timer(func=None, label=None):
    """
    Decorator to time function execution.
    
    Args:
        func: Function to decorate
        label: Optional label for the timer
        
    Returns:
        Decorated function
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Generate function signature for detailed logging
            func_name = fn.__name__
            module = fn.__module__
            
            # Use provided label or generate one
            metric_label = label or f"{module}.{func_name}"
            
            # Start timer
            start_time = time.time()
            
            # Call the function
            result = fn(*args, **kwargs)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Record metric
            record_performance_metric(
                metric_label,
                elapsed_time,
                "function_call"
            )
            
            return result
        return wrapper
        
    if func is None:
        # Called with parameters
        return decorator
    else:
        # Called without parameters
        return decorator(func)

def record_performance_metric(label, value, metric_type="custom"):
    """
    Record a performance metric.
    
    Args:
        label: Metric label
        value: Metric value
        metric_type: Type of metric
    """
    # Create the metric
    metric = {
        "timestamp": datetime.now().isoformat(),
        "label": label,
        "value": value,
        "type": metric_type
    }
    
    # Add user context if available
    if hasattr(st, "session_state") and "logged_in_user" in st.session_state:
        metric["user"] = st.session_state.logged_in_user
    
    # Add the metric to storage
    st.session_state.performance_metrics.append(metric)
    
    # Trim if too large
    if len(st.session_state.performance_metrics) > MAX_METRICS:
        st.session_state.performance_metrics = st.session_state.performance_metrics[-MAX_METRICS:]
    
    # Log slow operations
    if metric_type == "function_call" and value > 1.0:  # Log functions taking more than 1 second
        logging.warning(f"Slow operation detected: {label} took {value:.2f} seconds")

def time_block(label):
    """
    Context manager for timing a block of code.
    
    Args:
        label: Label for the timer
        
    Returns:
        Context manager
    """
    class TimerContext:
        def __enter__(self):
            self.start_time = time.time()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed_time = time.time() - self.start_time
            record_performance_metric(
                label,
                elapsed_time,
                "code_block"
            )
    
    return TimerContext()

def profile_database_queries(func):
    """
    Decorator to profile database queries.
    
    Args:
        func: Database query function to profile
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query = args[0] if args else kwargs.get('query', 'Unknown query')
        
        # Extract first line of query for label
        if isinstance(query, str):
            query_label = query.strip().split('\n')[0][:50]
            if len(query_label) < len(query.strip()):
                query_label += "..."
        else:
            query_label = "Non-string query"
        
        # Start timer
        start_time = time.time()
        
        # Call the function
        result = func(*args, **kwargs)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Record metric
        record_performance_metric(
            f"DB_QUERY: {query_label}",
            elapsed_time,
            "database_query"
        )
        
        return result
    return wrapper

def show_performance_dashboard():
    """Show admin interface for performance monitoring."""
    st.subheader("Performance Metrics")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        hours = st.slider("Past hours to analyze", 1, 24, 6)
    with col2:
        min_threshold = st.number_input("Min duration threshold (s)", 0.0, 10.0, 0.1, step=0.1)
    
    # Filter metrics by time
    start_time = datetime.now() - timedelta(hours=hours)
    
    # Get metrics
    metrics = st.session_state.performance_metrics
    
    if not metrics:
        st.info("No performance metrics recorded yet.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter by time and threshold
    df = df[df['timestamp'] >= start_time]
    df = df[df['value'] >= min_threshold]
    
    if df.empty:
        st.info("No metrics match your filters.")
        return
    
    # Display summary statistics
    st.subheader("Summary Statistics")
    
    # Group by label and calculate stats
    summary = df.groupby('label').agg({
        'value': ['count', 'mean', 'min', 'max', 'std']
    }).reset_index()
    
    # Flatten multi-level columns
    summary.columns = ['label', 'count', 'avg_duration', 'min_duration', 'max_duration', 'std_deviation']
    
    # Sort by average duration
    summary = summary.sort_values('avg_duration', ascending=False)
    
    # Format durations
    for col in ['avg_duration', 'min_duration', 'max_duration', 'std_deviation']:
        summary[col] = summary[col].round(3)
    
    # Display table
    st.dataframe(
        summary,
        column_config={
            "label": "Operation",
            "count": "Count",
            "avg_duration": st.column_config.NumberColumn(
                "Avg Duration (s)",
                format="%.3f s"
            ),
            "min_duration": st.column_config.NumberColumn(
                "Min Duration (s)",
                format="%.3f s"
            ),
            "max_duration": st.column_config.NumberColumn(
                "Max Duration (s)",
                format="%.3f s"
            ),
            "std_deviation": st.column_config.NumberColumn(
                "Std Dev",
                format="%.3f s"
            )
        },
        use_container_width=True
    )
    
    # Visualizations
    st.subheader("Performance Visualizations")
    
    # Time series chart
    st.write("Duration Over Time")
    
    fig1 = px.scatter(
        df,
        x='timestamp',
        y='value',
        color='label',
        hover_data=['label', 'type'],
        title='Operation Duration Over Time',
        labels={
            'timestamp': 'Time',
            'value': 'Duration (seconds)',
            'label': 'Operation'
        }
    )
    
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Box plot
    st.write("Duration Distribution by Operation")
    
    fig2 = px.box(
        df,
        x='label',
        y='value',
        title='Duration Distribution by Operation',
        labels={
            'label': 'Operation',
            'value': 'Duration (seconds)'
        }
    )
    
    fig2.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Group by type
    st.write("Performance by Operation Type")
    
    type_summary = df.groupby('type').agg({
        'value': ['count', 'mean', 'sum']
    }).reset_index()
    
    type_summary.columns = ['type', 'count', 'avg_duration', 'total_duration']
    
    fig3 = px.bar(
        type_summary,
        x='type',
        y='total_duration',
        title='Total Duration by Operation Type',
        text=type_summary['count'].astype(str) + ' calls',
        labels={
            'type': 'Operation Type',
            'total_duration': 'Total Duration (seconds)'
        }
    )
    
    fig3.update_layout(height=300)
    st.plotly_chart(fig3, use_container_width=True)
    
    # Slowest operations
    st.subheader("Slowest Individual Operations")
    
    slow_ops = df.sort_values('value', ascending=False).head(10)
    
    st.dataframe(
        slow_ops,
        column_config={
            "label": "Operation",
            "value": st.column_config.NumberColumn(
                "Duration (s)",
                format="%.3f s"
            ),
            "timestamp": st.column_config.DatetimeColumn(
                "Time",
                format="MMM DD, YYYY, hh:mm:ss a"
            ),
            "type": "Type",
            "user": "User"
        },
        use_container_width=True
    )