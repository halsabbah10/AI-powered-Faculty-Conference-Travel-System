"""
User feedback module.
Handles collection and storage of user feedback.
"""

import streamlit as st
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px

from app.database.connection import DatabaseManager
from app.ui.common import display_success_box, display_error_box

def create_feedback_table():
    """Create feedback table if it doesn't exist."""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS user_feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            page VARCHAR(100),
            rating INT,
            feedback_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        DatabaseManager.execute_query(query, fetch=False, commit=True)
    except Exception as e:
        logging.error(f"Error creating feedback table: {str(e)}")

def save_feedback(user_id, page, rating, feedback_text):
    """
    Save user feedback to database.
    
    Args:
        user_id: ID of the user providing feedback
        page: Page or feature being rated
        rating: Numerical rating (1-5)
        feedback_text: Text feedback
        
    Returns:
        bool: Success status
    """
    try:
        query = """
        INSERT INTO user_feedback (user_id, page, rating, feedback_text)
        VALUES (%s, %s, %s, %s)
        """
        
        DatabaseManager.execute_query(
            query, 
            (user_id, page, rating, feedback_text),
            fetch=False,
            commit=True
        )
        
        logging.info(f"Feedback saved for user {user_id} on page {page}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving feedback: {str(e)}")
        return False

def get_feedback_stats():
    """
    Get statistics on user feedback.
    
    Returns:
        dict: Feedback statistics
    """
    try:
        query = """
        SELECT 
            page, 
            AVG(rating) as avg_rating,
            COUNT(*) as count
        FROM user_feedback
        GROUP BY page
        ORDER BY avg_rating DESC
        """
        
        results = DatabaseManager.execute_query(query)
        
        # Get recent feedback
        recent_query = """
        SELECT 
            user_id, 
            page, 
            rating, 
            feedback_text,
            created_at
        FROM user_feedback
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        recent = DatabaseManager.execute_query(recent_query)
        
        return {
            "page_stats": results,
            "recent_feedback": recent
        }
        
    except Exception as e:
        logging.error(f"Error getting feedback stats: {str(e)}")
        return {
            "page_stats": [],
            "recent_feedback": []
        }

def show_feedback_form(page_name):
    """
    Display feedback form for the current page.
    
    Args:
        page_name: Name of the current page
    """
    with st.expander("Provide Feedback", expanded=False):
        st.write("Help us improve by sharing your feedback!")
        
        with st.form(key=f"feedback_form_{page_name}"):
            rating = st.slider(
                "Rate your experience",
                min_value=1,
                max_value=5,
                value=4,
                help="1 = Poor, 5 = Excellent"
            )
            
            feedback_text = st.text_area(
                "Comments (optional)",
                placeholder="Share your thoughts or suggestions..."
            )
            
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                if "logged_in_user" not in st.session_state:
                    user_id = "anonymous"
                else:
                    user_id = st.session_state.logged_in_user
                
                # Create table if needed
                create_feedback_table()
                
                # Save feedback
                success = save_feedback(
                    user_id,
                    page_name,
                    rating,
                    feedback_text
                )
                
                if success:
                    display_success_box("Thank you for your feedback!")
                else:
                    display_error_box("There was an error saving your feedback. Please try again.")

def show_feedback_dashboard():
    """Display feedback statistics dashboard."""
    st.subheader("User Feedback Dashboard")
    
    # Get feedback stats
    stats = get_feedback_stats()
    
    if not stats["page_stats"]:
        st.info("No feedback data available yet.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(stats["page_stats"])
    
    # Display average ratings
    st.subheader("Average Ratings by Page")
    
    fig = px.bar(
        df,
        x="page",
        y="avg_rating",
        color="avg_rating",
        text="count",
        labels={
            "page": "Page",
            "avg_rating": "Average Rating",
            "count": "Number of Ratings"
        },
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    fig.update_layout(
        xaxis_title="Page",
        yaxis_title="Average Rating",
        yaxis_range=[0, 5]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display recent feedback
    st.subheader("Recent Feedback")
    
    if stats["recent_feedback"]:
        recent_df = pd.DataFrame(stats["recent_feedback"])
        
        # Format dates
        recent_df['created_at'] = pd.to_datetime(recent_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display in table
        st.dataframe(
            recent_df,
            column_config={
                "user_id": "User",
                "page": "Page",
                "rating": st.column_config.NumberColumn(
                    "Rating",
                    help="1 = Poor, 5 = Excellent",
                    format="%d ⭐"
                ),
                "feedback_text": "Feedback",
                "created_at": "Submitted On"
            },
            use_container_width=True
        )
    else:
        st.info("No recent feedback available.")