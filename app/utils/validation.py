"""
Validation utility module.
Provides standardized validation for forms and data.
"""

import re
import streamlit as st
from datetime import datetime
from app.utils.internationalization import t
from app.utils.error_handling import ValidationError, raise_validation_error

class Validator:
    """Validation utility class for form input and data validation."""
    
    @staticmethod
    def required(value, message=None):
        """
        Validate that a value is not empty.
        
        Args:
            value: Value to validate
            message: Optional custom error message
            
        Returns:
            bool or str: True if valid, error message if invalid
        """
        # Handle different types of emptiness
        if value is None:
            return message or t("validation.required", "This field is required")
        
        if isinstance(value, str) and value.strip() == "":
            return message or t("validation.required", "This field is required")
        
        if isinstance(value, (list, dict)) and len(value) == 0:
            return message or t("validation.required", "This field is required")
            
        return True
    
    @staticmethod
    def min_length(min_len, message=None):
        """
        Create a validator for minimum string length.
        
        Args:
            min_len: Minimum length required
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        def validator(value):
            if not value or not isinstance(value, str):
                return True  # Skip validation if empty (use required validator for that)
                
            if len(value) < min_len:
                return message or t("validation.min_length", "Must be at least {0} characters").format(min_len)
                
            return True
            
        return validator
    
    @staticmethod
    def max_length(max_len, message=None):
        """
        Create a validator for maximum string length.
        
        Args:
            max_len: Maximum length allowed
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        def validator(value):
            if not value or not isinstance(value, str):
                return True  # Skip validation if empty
                
            if len(value) > max_len:
                return message or t("validation.max_length", "Must be at most {0} characters").format(max_len)
                
            return True
            
        return validator
    
    @staticmethod
    def pattern(regex, message=None):
        """
        Create a validator for regex pattern matching.
        
        Args:
            regex: Regular expression pattern
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        def validator(value):
            if not value or not isinstance(value, str):
                return True  # Skip validation if empty
                
            if not re.match(regex, value):
                return message or t("validation.pattern", "Invalid format")
                
            return True
            
        return validator
    
    @staticmethod
    def email(message=None):
        """
        Create a validator for email format.
        
        Args:
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return Validator.pattern(email_pattern, message or t("validation.email", "Invalid email address"))
    
    @staticmethod
    def url(message=None):
        """
        Create a validator for URL format.
        
        Args:
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        url_pattern = r'^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$'
        return Validator.pattern(url_pattern, message or t("validation.url", "Invalid URL format"))
    
    @staticmethod
    def min_value(min_val, message=None):
        """
        Create a validator for minimum numeric value.
        
        Args:
            min_val: Minimum value allowed
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        def validator(value):
            if value is None:
                return True  # Skip validation if empty
                
            try:
                # Convert to float for comparison
                num_value = float(value)
                if num_value < min_val:
                    return message or t("validation.min_value", "Must be at least {0}").format(min_val)
            except (ValueError, TypeError):
                return t("validation.number", "Must be a number")
                
            return True
            
        return validator
    
    @staticmethod
    def max_value(max_val, message=None):
        """
        Create a validator for maximum numeric value.
        
        Args:
            max_val: Maximum value allowed
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        def validator(value):
            if value is None:
                return True  # Skip validation if empty
                
            try:
                # Convert to float for comparison
                num_value = float(value)
                if num_value > max_val:
                    return message or t("validation.max_value", "Must be at most {0}").format(max_val)
            except (ValueError, TypeError):
                return t("validation.number", "Must be a number")
                
            return True
            
        return validator
    
    @staticmethod
    def date_range(start_date=None, end_date=None, message=None):
        """
        Create a validator for date range.
        
        Args:
            start_date: Minimum date allowed
            end_date: Maximum date allowed
            message: Optional custom error message
            
        Returns:
            function: Validator function
        """
        def validator(value):
            if value is None:
                return True  # Skip validation if empty
                
            if not isinstance(value, datetime.date):
                return t("validation.date", "Must be a valid date")
                
            if start_date and value < start_date:
                return message or t("validation.date_min", "Date must be on or after {0}").format(start_date.strftime("%Y-%m-%d"))
                
            if end_date and value > end_date:
                return message or t("validation.date_max", "Date must be on or before {0}").format(end_date.strftime("%Y-%m-%d"))
                
            return True
            
        return validator
    
    @staticmethod
    def validate_form(form_data, validators):
        """
        Validate a form with multiple field validators.
        
        Args:
            form_data: Dictionary of form field values
            validators: Dictionary mapping field names to validators
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = {}
        
        for field, field_validators in validators.items():
            if field not in form_data:
                continue
            
            value = form_data[field]
            
            # Apply each validator for this field
            for validator in field_validators:
                result = validator(value)
                
                if result is not True:
                    errors[field] = result
                    break
        
        return len(errors) == 0, errors

def display_form_errors(errors):
    """
    Display form validation errors in the UI.
    
    Args:
        errors: Dictionary of field/error pairs or error message
    """
    if isinstance(errors, dict):
        for field, error in errors.items():
            st.error(f"{field}: {error}")
    elif isinstance(errors, list):
        for error in errors:
            st.error(error)
    else:
        st.error(str(errors))

# Common validation functions
def validate_conference_input(conference_name, conference_url, start_date, end_date):
    """
    Validate conference input data.
    
    Args:
        conference_name: Conference name
        conference_url: Conference URL
        start_date: Start date
        end_date: End date
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not conference_name or len(conference_name) < 3:
        return False, t("validation.conference_name", "Conference name must be at least 3 characters")
        
    if conference_url and not (conference_url.startswith("http://") or conference_url.startswith("https://")):
        return False, t("validation.conference_url", "Please enter a valid URL starting with http:// or https://")
        
    if start_date and end_date and start_date > end_date:
        return False, t("validation.date_range", "End date must be after start date")
        
    return True, ""

def validate_budget_input(budget_data):
    """
    Validate budget input data.
    
    Args:
        budget_data: Budget form data
        
    Returns:
        tuple: (is_valid, errors)
    """
    errors = {}
    
    # Required fields
    required_fields = ['department', 'year', 'amount']
    for field in required_fields:
        if field not in budget_data or not budget_data[field]:
            errors[field] = t("validation.required", "This field is required")
    
    # Validate year
    if 'year' in budget_data and budget_data['year']:
        try:
            year = int(budget_data['year'])
            current_year = datetime.now().year
            if year < current_year - 1 or year > current_year + 5:
                errors['year'] = t("validation.year_range", "Year must be between {0} and {1}").format(
                    current_year - 1, current_year + 5
                )
        except (ValueError, TypeError):
            errors['year'] = t("validation.year_format", "Year must be a valid number")
    
    # Validate amount
    if 'amount' in budget_data and budget_data['amount']:
        try:
            amount = float(budget_data['amount'])
            if amount <= 0:
                errors['amount'] = t("validation.amount_positive", "Amount must be positive")
        except (ValueError, TypeError):
            errors['amount'] = t("validation.amount_format", "Amount must be a valid number")
    
    return len(errors) == 0, errors