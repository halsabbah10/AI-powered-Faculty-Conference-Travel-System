"""
Validation utility module.
Provides reusable validation functions for form data.
"""

import re
from datetime import datetime, date
from urllib.parse import urlparse
import streamlit as st
from app.utils.error_handling import ValidationError

class Validator:
    """Utility class for validating data."""
    
    @staticmethod
    def required(value, field_name=None, message=None):
        """
        Validate that a value is not empty.
        
        Args:
            value: Value to validate
            field_name: Optional field name for error message
            message: Optional custom error message
            
        Returns:
            bool or str: True if valid, error message if invalid
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return message or f"{field_name or 'This field'} is required"
        return True
    
    @staticmethod
    def min_length(min_length):
        """
        Create validator for minimum string length.
        
        Args:
            min_length: Minimum required length
            
        Returns:
            function: Validator function
        """
        def validator(value, field_name=None, message=None):
            if not value or len(str(value)) < min_length:
                return message or f"{field_name or 'This field'} must be at least {min_length} characters"
            return True
        return validator
    
    @staticmethod
    def max_length(max_length):
        """
        Create validator for maximum string length.
        
        Args:
            max_length: Maximum allowed length
            
        Returns:
            function: Validator function
        """
        def validator(value, field_name=None, message=None):
            if value and len(str(value)) > max_length:
                return message or f"{field_name or 'This field'} must be at most {max_length} characters"
            return True
        return validator
    
    @staticmethod
    def email(value, field_name=None, message=None):
        """
        Validate email format.
        
        Args:
            value: Value to validate
            field_name: Optional field name for error message
            message: Optional custom error message
            
        Returns:
            bool or str: True if valid, error message if invalid
        """
        if not value:
            return True  # Skip validation if empty (use required validator if necessary)
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return message or f"{field_name or 'Email'} is not a valid email address"
        return True
    
    @staticmethod
    def url(value, field_name=None, message=None, require_https=False):
        """
        Validate URL format.
        
        Args:
            value: Value to validate
            field_name: Optional field name for error message
            message: Optional custom error message
            require_https: Whether to require HTTPS
            
        Returns:
            bool or str: True if valid, error message if invalid
        """
        if not value:
            return True  # Skip validation if empty
        
        try:
            result = urlparse(value)
            valid = all([result.scheme, result.netloc])
            
            if require_https and result.scheme != 'https':
                return message or f"{field_name or 'URL'} must use HTTPS"
                
            if not valid:
                return message or f"{field_name or 'URL'} is not a valid URL"
                
            return True
        except:
            return message or f"{field_name or 'URL'} is not a valid URL"
    
    @staticmethod
    def date_range(start_date, end_date, field_name=None, message=None):
        """
        Validate date range (start must be before or equal to end).
        
        Args:
            start_date: Start date
            end_date: End date
            field_name: Optional field name for error message
            message: Optional custom error message
            
        Returns:
            bool or str: True if valid, error message if invalid
        """
        if not start_date or not end_date:
            return True  # Skip validation if either date is missing
        
        # Convert strings to date objects if needed
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except:
                return f"Invalid start date format"
        
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                return f"Invalid end date format"
        
        # Ensure both are date objects
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        if start_date > end_date:
            return message or f"{field_name or 'End date'} must be after start date"
        return True
    
    @staticmethod
    def numeric(value, field_name=None, message=None):
        """
        Validate that value is numeric.
        
        Args:
            value: Value to validate
            field_name: Optional field name for error message
            message: Optional custom error message
            
        Returns:
            bool or str: True if valid, error message if invalid
        """
        if not value:
            return True  # Skip validation if empty
        
        try:
            float(value)
            return True
        except:
            return message or f"{field_name or 'This field'} must be a number"
    
    @staticmethod
    def number_range(min_val=None, max_val=None):
        """
        Create validator for number range.
        
        Args:
            min_val: Minimum allowed value (or None for no minimum)
            max_val: Maximum allowed value (or None for no maximum)
            
        Returns:
            function: Validator function
        """
        def validator(value, field_name=None, message=None):
            if not value:
                return True  # Skip validation if empty
            
            try:
                num_value = float(value)
                
                if min_val is not None and num_value < min_val:
                    return message or f"{field_name or 'This field'} must be at least {min_val}"
                
                if max_val is not None and num_value > max_val:
                    return message or f"{field_name or 'This field'} must be at most {max_val}"
                
                return True
            except:
                return f"{field_name or 'This field'} must be a number"
        return validator
    
    @staticmethod
    def file_size(max_size_mb):
        """
        Create validator for file size.
        
        Args:
            max_size_mb: Maximum file size in megabytes
            
        Returns:
            function: Validator function
        """
        def validator(file, field_name=None, message=None):
            if not file:
                return True  # Skip validation if no file
            
            max_bytes = max_size_mb * 1024 * 1024
            
            if hasattr(file, 'size'):
                # Streamlit UploadedFile
                if file.size > max_bytes:
                    return message or f"{field_name or 'File'} size exceeds the maximum of {max_size_mb}MB"
            elif isinstance(file, bytes):
                # Raw bytes
                if len(file) > max_bytes:
                    return message or f"{field_name or 'File'} size exceeds the maximum of {max_size_mb}MB"
            
            return True
        return validator
    
    @staticmethod
    def file_type(allowed_types):
        """
        Create validator for file type.
        
        Args:
            allowed_types: List of allowed MIME types or extensions
            
        Returns:
            function: Validator function
        """
        def validator(file, field_name=None, message=None):
            if not file:
                return True  # Skip validation if no file
            
            if hasattr(file, 'type') and file.type:
                # Check MIME type
                file_type = file.type
                
                if not any(allowed in file_type.lower() for allowed in allowed_types):
                    types_str = ", ".join(allowed_types)
                    return message or f"{field_name or 'File'} type must be one of: {types_str}"
            elif hasattr(file, 'name') and file.name:
                # Check extension
                file_ext = file.name.split('.')[-1].lower()
                
                if not any(ext.lower() == file_ext or ext.lower() == f".{file_ext}" for ext in allowed_types):
                    types_str = ", ".join(allowed_types)
                    return message or f"{field_name or 'File'} type must be one of: {types_str}"
            
            return True
        return validator
    
    @staticmethod
    def validate_form(data, validators):
        """
        Validate form data using validators.
        
        Args:
            data: Dictionary of form data
            validators: Dictionary of field validators {field_name: validator_function}
            
        Returns:
            tuple: (is_valid, errors)
            
        Example:
            validators = {
                'name': [Validator.required, Validator.min_length(3)],
                'email': [Validator.required, Validator.email],
                'age': [Validator.numeric, Validator.number_range(18, 120)]
            }
            is_valid, errors = Validator.validate_form(form_data, validators)
        """
        errors = {}
        
        for field_name, field_validators in validators.items():
            if not isinstance(field_validators, list):
                field_validators = [field_validators]
            
            value = data.get(field_name)
            
            for validator in field_validators:
                result = validator(value, field_name)
                
                if result is not True:
                    errors[field_name] = result
                    break
        
        return len(errors) == 0, errors

    @staticmethod
    def validate_or_raise(data, validators):
        """
        Validate form data and raise ValidationError if invalid.
        
        Args:
            data: Dictionary of form data
            validators: Dictionary of field validators
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        is_valid, errors = Validator.validate_form(data, validators)
        
        if not is_valid:
            if len(errors) == 1:
                field_name = list(errors.keys())[0]
                raise ValidationError(errors[field_name], field=field_name)
            else:
                raise ValidationError("Form validation failed", details=errors)
        
        return True


def validate_conference_input(data):
    """
    Validate conference input form data.
    
    Args:
        data: Dictionary with conference form data
        
    Returns:
        tuple: (is_valid, errors)
    """
    validators = {
        'conference_name': [
            Validator.required,
            Validator.min_length(3)
        ],
        'conference_url': [
            Validator.required,
            Validator.url
        ],
        'destination': [
            Validator.required
        ],
        'city': [
            Validator.required
        ]
    }
    
    is_valid, errors = Validator.validate_form(data, validators)
    
    # Custom date range validation
    if 'date_from' in data and 'date_to' in data:
        date_result = Validator.date_range(
            data.get('date_from'), 
            data.get('date_to'),
            "Date range"
        )
        
        if date_result is not True:
            is_valid = False
            errors['date_to'] = date_result
    
    return is_valid, errors


def validate_document_upload(data):
    """
    Validate document upload form data.
    
    Args:
        data: Dictionary with document form data
        
    Returns:
        tuple: (is_valid, errors)
    """
    validators = {
        'file': [
            Validator.required,
            Validator.file_size(10),  # 10MB max
            Validator.file_type(['pdf', 'docx', 'doc', 'txt', 'application/pdf', 
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
        ],
        'description': [
            Validator.required,
            Validator.min_length(5),
            Validator.max_length(200)
        ]
    }
    
    return Validator.validate_form(data, validators)


def validate_budget_input(data):
    """
    Validate budget form data.
    
    Args:
        data: Dictionary with budget form data
        
    Returns:
        tuple: (is_valid, errors)
    """
    validators = {
        'department': [Validator.required],
        'year': [
            Validator.required,
            Validator.numeric,
            Validator.number_range(2000, 2100)
        ],
        'quarter': [
            Validator.required,
            Validator.numeric,
            Validator.number_range(1, 4)
        ],
        'amount': [
            Validator.required,
            Validator.numeric,
            Validator.number_range(0, None)
        ]
    }
    
    return Validator.validate_form(data, validators)


def display_form_errors(errors):
    """
    Display form validation errors in Streamlit.
    
    Args:
        errors: Dictionary of field/error pairs
    """
    for field, error in errors.items():
        st.error(f"{field}: {error}")