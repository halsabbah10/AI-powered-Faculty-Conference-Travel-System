"""
Email notification service.
Handles sending email notifications for various system events.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@example.com")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"

def send_email(to_email, subject, html_content, text_content=None):
    """
    Send an email with HTML and optional plain text content.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (falls back to HTML with tags removed)
        
    Returns:
        bool: Success status
    """
    if not EMAIL_ENABLED:
        logging.info(f"Email sending disabled. Would send to {to_email}: {subject}")
        return True
        
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logging.error("Email credentials not configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        
        # Create plain text version if not provided
        if text_content is None:
            # Simple conversion by removing HTML tags
            import re
            text_content = re.sub(r'<.*?>', '', html_content)
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Send email
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        server.quit()
        
        logging.info(f"Email sent to {to_email}: {subject}")
        return True
        
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False

def send_request_submission_notification(request_id, faculty_email, faculty_name, conference_name):
    """Send notification when a request is submitted."""
    subject = f"Request Submitted: {request_id}"
    
    html_content = f"""
    <html>
    <body>
        <h2>Conference Travel Request Submitted</h2>
        <p>Dear {faculty_name},</p>
        <p>Your request to attend <strong>{conference_name}</strong> has been submitted successfully.</p>
        <p>Request ID: <strong>{request_id}</strong></p>
        <p>Your request will be reviewed by the approval authority. You will be notified when a decision is made.</p>
        <p>Thank you,<br>Faculty Conference Travel System</p>
    </body>
    </html>
    """
    
    return send_email(faculty_email, subject, html_content)

def send_request_status_notification(request_id, faculty_email, faculty_name, conference_name, status, notes=None):
    """Send notification when a request status changes."""
    subject = f"Request {status.capitalize()}: {request_id}"
    
    status_color = "#28a745" if status == "approved" else "#dc3545"
    status_text = status.capitalize()
    
    html_content = f"""
    <html>
    <body>
        <h2>Conference Travel Request {status_text}</h2>
        <p>Dear {faculty_name},</p>
        <p>Your request to attend <strong>{conference_name}</strong> has been <span style="color: {status_color}; font-weight: bold;">{status_text}</span>.</p>
        <p>Request ID: <strong>{request_id}</strong></p>
    """
    
    if notes:
        html_content += f"<p><strong>Notes:</strong> {notes}</p>"
    
    html_content += f"""
        <p>For more details, please log in to the Faculty Conference Travel System.</p>
        <p>Thank you,<br>Faculty Conference Travel System</p>
    </body>
    </html>
    """
    
    return send_email(faculty_email, subject, html_content)

def send_pending_approval_notification(approver_email, approver_name, request_id, faculty_name, conference_name):
    """Send notification to approver about pending request."""
    subject = f"Request Pending Approval: {request_id}"
    
    html_content = f"""
    <html>
    <body>
        <h2>Conference Travel Request Pending Approval</h2>
        <p>Dear {approver_name},</p>
        <p>A new travel request requires your review:</p>
        <ul>
            <li>Request ID: <strong>{request_id}</strong></li>
            <li>Faculty: <strong>{faculty_name}</strong></li>
            <li>Conference: <strong>{conference_name}</strong></li>
        </ul>
        <p>Please log in to the Faculty Conference Travel System to review and make a decision.</p>
        <p>Thank you,<br>Faculty Conference Travel System</p>
    </body>
    </html>
    """
    
    return send_email(approver_email, subject, html_content)

def send_budget_alert(admin_email, admin_name, remaining_budget, threshold_percentage):
    """Send alert when budget falls below threshold."""
    subject = f"Budget Alert: Remaining Budget Below {threshold_percentage}%"
    
    html_content = f"""
    <html>
    <body>
        <h2>Budget Alert</h2>
        <p>Dear {admin_name},</p>
        <p>This is to inform you that the remaining budget for conference travel has fallen below <strong>{threshold_percentage}%</strong>.</p>
        <p>Current remaining budget: <strong>${remaining_budget:.2f}</strong></p>
        <p>Please log in to the Faculty Conference Travel System to review the budget and make any necessary adjustments.</p>
        <p>Thank you,<br>Faculty Conference Travel System</p>
    </body>
    </html>
    """
    
    return send_email(admin_email, subject, html_content)