"""
Notification service module.
Provides real-time notifications functionality.
"""

import json
import logging
import time
import threading
import os
from datetime import datetime
import streamlit as st
from pathlib import Path

# Default notifications directory
NOTIFICATIONS_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "data" / "notifications"

# Ensure directory exists
NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

class NotificationService:
    """Service for managing user notifications."""
    
    @staticmethod
    def create_notification(user_id, message, notification_type="info", related_id=None, data=None):
        """
        Create a new notification for a user.
        
        Args:
            user_id: ID of the recipient user
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            related_id: Optional ID of related entity (e.g., request_id)
            data: Optional additional data
            
        Returns:
            str: Notification ID
        """
        try:
            # Create notification object
            notification = {
                "id": int(time.time() * 1000),  # Use timestamp as ID
                "user_id": user_id,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            
            # Add optional fields
            if related_id:
                notification["related_id"] = related_id
                
            if data:
                notification["data"] = data
            
            # Get user's notification file path
            user_file = NOTIFICATIONS_DIR / f"{user_id}.json"
            
            # Load existing notifications or create empty list
            notifications = []
            if user_file.exists():
                try:
                    with open(user_file, 'r') as f:
                        notifications = json.load(f)
                except json.JSONDecodeError:
                    # Handle corrupted file
                    notifications = []
            
            # Add new notification
            notifications.append(notification)
            
            # Limit to 100 notifications per user
            if len(notifications) > 100:
                notifications = sorted(notifications, key=lambda x: x["id"], reverse=True)[:100]
            
            # Save notifications
            with open(user_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            # Add to active session if user is logged in
            if hasattr(st, "session_state") and "logged_in_user" in st.session_state:
                if st.session_state.logged_in_user == user_id:
                    if "notifications" not in st.session_state:
                        st.session_state.notifications = []
                    
                    st.session_state.notifications.append(notification)
                    
                    # Update unread count
                    if "unread_notifications" not in st.session_state:
                        st.session_state.unread_notifications = 0
                    
                    st.session_state.unread_notifications += 1
            
            return str(notification["id"])
            
        except Exception as e:
            logging.error(f"Error creating notification: {str(e)}")
            return None
    
    @staticmethod
    def get_notifications(user_id, include_read=False, limit=20):
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of the user
            include_read: Whether to include read notifications
            limit: Maximum number of notifications to return
            
        Returns:
            list: User's notifications
        """
        try:
            user_file = NOTIFICATIONS_DIR / f"{user_id}.json"
            
            # Return empty list if file doesn't exist
            if not user_file.exists():
                return []
            
            # Load notifications
            with open(user_file, 'r') as f:
                notifications = json.load(f)
            
            # Filter and sort
            if not include_read:
                notifications = [n for n in notifications if not n.get("read", False)]
                
            # Sort by timestamp (newest first)
            notifications = sorted(notifications, key=lambda x: x["id"], reverse=True)
            
            # Apply limit
            if limit > 0:
                notifications = notifications[:limit]
            
            return notifications
            
        except Exception as e:
            logging.error(f"Error getting notifications: {str(e)}")
            return []
    
    @staticmethod
    def mark_as_read(user_id, notification_id=None):
        """
        Mark notifications as read.
        
        Args:
            user_id: ID of the user
            notification_id: Optional specific notification ID to mark as read
                             If None, all notifications are marked as read
            
        Returns:
            bool: Success status
        """
        try:
            user_file = NOTIFICATIONS_DIR / f"{user_id}.json"
            
            # Return success if file doesn't exist
            if not user_file.exists():
                return True
            
            # Load notifications
            with open(user_file, 'r') as f:
                notifications = json.load(f)
            
            # Mark specific notification or all
            modified = False
            for notification in notifications:
                if notification_id is None or str(notification.get("id", "")) == str(notification_id):
                    if not notification.get("read", False):
                        notification["read"] = True
                        modified = True
            
            # Save if modified
            if modified:
                with open(user_file, 'w') as f:
                    json.dump(notifications, f, indent=2)
                
                # Update session state
                if hasattr(st, "session_state") and "logged_in_user" in st.session_state:
                    if st.session_state.logged_in_user == user_id:
                        if "notifications" in st.session_state:
                            for notification in st.session_state.notifications:
                                if notification_id is None or str(notification.get("id", "")) == str(notification_id):
                                    notification["read"] = True
                        
                        # Reset unread count
                        if notification_id is None:
                            st.session_state.unread_notifications = 0
                        elif "unread_notifications" in st.session_state and st.session_state.unread_notifications > 0:
                            st.session_state.unread_notifications -= 1
            
            return True
            
        except Exception as e:
            logging.error(f"Error marking notifications as read: {str(e)}")
            return False
    
    @staticmethod
    def delete_notification(user_id, notification_id):
        """
        Delete a notification.
        
        Args:
            user_id: ID of the user
            notification_id: ID of the notification to delete
            
        Returns:
            bool: Success status
        """
        try:
            user_file = NOTIFICATIONS_DIR / f"{user_id}.json"
            
            # Return success if file doesn't exist
            if not user_file.exists():
                return True
            
            # Load notifications
            with open(user_file, 'r') as f:
                notifications = json.load(f)
            
            # Find and remove notification
            notification_id = str(notification_id)
            original_len = len(notifications)
            notifications = [n for n in notifications if str(n.get("id", "")) != notification_id]
            
            # Save if modified
            if len(notifications) < original_len:
                with open(user_file, 'w') as f:
                    json.dump(notifications, f, indent=2)
                
                # Update session state
                if hasattr(st, "session_state") and "logged_in_user" in st.session_state:
                    if st.session_state.logged_in_user == user_id:
                        if "notifications" in st.session_state:
                            # Check if the notification was unread
                            was_unread = any(
                                str(n.get("id", "")) == notification_id and not n.get("read", False)
                                for n in st.session_state.notifications
                            )
                            
                            # Update notifications list
                            st.session_state.notifications = [
                                n for n in st.session_state.notifications
                                if str(n.get("id", "")) != notification_id
                            ]
                            
                            # Update unread count
                            if was_unread and "unread_notifications" in st.session_state and st.session_state.unread_notifications > 0:
                                st.session_state.unread_notifications -= 1
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting notification: {str(e)}")
            return False

def display_notifications():
    """Display notification panel in the UI."""
    # Initialize notifications in session state
    if "notifications" not in st.session_state:
        if "logged_in_user" in st.session_state:
            # Load notifications for current user
            st.session_state.notifications = NotificationService.get_notifications(
                st.session_state.logged_in_user,
                include_read=True,
                limit=20
            )
            
            # Count unread
            st.session_state.unread_notifications = sum(
                1 for n in st.session_state.notifications if not n.get("read", False)
            )
        else:
            st.session_state.notifications = []
            st.session_state.unread_notifications = 0
    
    # Create notification bell with counter
    unread_count = st.session_state.get("unread_notifications", 0)
    bell_label = f"🔔 ({unread_count})" if unread_count > 0 else "🔔"
    
    if st.sidebar.button(bell_label, key="notification_bell"):
        st.session_state.show_notifications = not st.session_state.get("show_notifications", False)
    
    # Show notification panel if toggled
    if st.session_state.get("show_notifications", False):
        with st.sidebar:
            st.markdown("### Notifications")
            
            if not st.session_state.notifications:
                st.info("No notifications")
            else:
                # Mark all as read button
                if st.button("Mark all as read"):
                    NotificationService.mark_as_read(st.session_state.logged_in_user)
                    # Update session state
                    for notification in st.session_state.notifications:
                        notification["read"] = True
                    st.session_state.unread_notifications = 0
                    st.experimental_rerun()
                
                # Display notifications
                for notification in st.session_state.notifications:
                    # Format timestamp
                    timestamp = datetime.fromisoformat(notification.get("timestamp", ""))
                    formatted_time = timestamp.strftime("%m/%d/%Y %H:%M")
                    
                    # Select background color based on type and read status
                    bg_color = "#EFF6FF" if notification.get("type") == "info" else "#ECFDF5"
                    if notification.get("type") == "warning":
                        bg_color = "#FEF3C7"
                    elif notification.get("type") == "error":
                        bg_color = "#FEE2E2"
                    
                    # Darker color for unread
                    if not notification.get("read", False):
                        bg_color = "#DBEAFE" if notification.get("type") == "info" else "#D1FAE5"
                        if notification.get("type") == "warning":
                            bg_color = "#FDE68A"
                        elif notification.get("type") == "error":
                            bg_color = "#FCA5A5"
                    
                    # Display notification
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {bg_color}; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 0.25rem;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                <span style="font-size: 0.75rem; color: #4B5563;">{formatted_time}</span>
                                <span style="font-size: 0.75rem; font-weight: bold; color: #4B5563;">
                                    {notification.get("type", "info").upper()}
                                </span>
                            </div>
                            <p style="margin: 0; font-size: 0.875rem;">
                                {notification.get("message", "")}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        cols = st.columns([1, 1])
                        
                        with cols[0]:
                            # Mark as read button for unread notifications
                            if not notification.get("read", False):
                                if st.button("Mark read", key=f"read_{notification['id']}"):
                                    NotificationService.mark_as_read(
                                        st.session_state.logged_in_user,
                                        notification["id"]
                                    )
                                    # Update notification in session state
                                    notification["read"] = True
                                    # Update unread count
                                    st.session_state.unread_notifications -= 1
                                    st.experimental_rerun()
                        
                        with cols[1]:
                            # Delete button
                            if st.button("Delete", key=f"delete_{notification['id']}"):
                                NotificationService.delete_notification(
                                    st.session_state.logged_in_user,
                                    notification["id"]
                                )
                                # Remove from session state
                                st.session_state.notifications.remove(notification)
                                # Update unread count if was unread
                                if not notification.get("read", False):
                                    st.session_state.unread_notifications -= 1
                                st.experimental_rerun()

def check_for_notifications():
    """
    Check for new notifications.
    Called periodically to update notification panel.
    """
    if "logged_in_user" in st.session_state:
        # This would normally pull from a database or message queue
        # For now, we'll just check the file
        user_file = NOTIFICATIONS_DIR / f"{st.session_state.logged_in_user}.json"
        
        if user_file.exists():
            try:
                # Get file modification time
                mod_time = os.path.getmtime(user_file)
                
                # Check if newer than our last check
                last_check = st.session_state.get("last_notification_check", 0)
                
                if mod_time > last_check:
                    # Reload notifications
                    with open(user_file, 'r') as f:
                        notifications = json.load(f)
                    
                    # Update session state
                    st.session_state.notifications = notifications
                    
                    # Count unread
                    st.session_state.unread_notifications = sum(
                        1 for n in notifications if not n.get("read", False)
                    )
                    
                    # Update last check time
                    st.session_state.last_notification_check = time.time()
                    
            except Exception as e:
                logging.error(f"Error checking for notifications: {str(e)}")

def create_notification_examples():
    """Generate example notifications for testing."""
    if "logged_in_user" in st.session_state:
        user_id = st.session_state.logged_in_user
        
        NotificationService.create_notification(
            user_id,
            "A new travel request has been submitted for your review.",
            "info",
            related_id="REQ12345"
        )
        
        NotificationService.create_notification(
            user_id,
            "Your travel request has been approved!",
            "success",
            related_id="REQ12345"
        )
        
        NotificationService.create_notification(
            user_id,
            "Budget alert: Department budget is below 20%",
            "warning"
        )