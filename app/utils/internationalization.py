"""
Internationalization module.
Provides multi-language support for the application.
"""

import os
import json
import streamlit as st
import logging
from functools import lru_cache
from pathlib import Path

# Base directory for localization files
LOCALE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "locales"

# Ensure locale directory exists
LOCALE_DIR.mkdir(exist_ok=True)

# Available languages with their display names
AVAILABLE_LANGUAGES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "zh": "中文",
    "ar": "العربية"
}

# Default language
DEFAULT_LANGUAGE = "en"

@lru_cache(maxsize=10)
def load_language_data(lang_code):
    """
    Load language strings for a specific language.
    Caches results for performance.
    
    Args:
        lang_code: Language code (e.g., 'en', 'es')
        
    Returns:
        dict: Language strings or empty dict if not found
    """
    try:
        lang_file = LOCALE_DIR / f"{lang_code}.json"
        
        # If language file doesn't exist, create it with default content
        if not lang_file.exists() and lang_code != DEFAULT_LANGUAGE:
            # Try to copy from default language first
            default_file = LOCALE_DIR / f"{DEFAULT_LANGUAGE}.json"
            if default_file.exists():
                with open(default_file, 'r', encoding='utf-8') as f:
                    lang_data = json.load(f)
                with open(lang_file, 'w', encoding='utf-8') as f:
                    json.dump(lang_data, f, ensure_ascii=False, indent=2)
            else:
                # Create empty template
                with open(lang_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
        
        # Load language file if it exists
        if lang_file.exists():
            with open(lang_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
            
    except Exception as e:
        logging.error(f"Error loading language file for '{lang_code}': {str(e)}")
        return {}

def init_localization():
    """
    Initialize localization settings.
    Creates default language files if they don't exist.
    """
    try:
        # Ensure default English language file exists
        default_file = LOCALE_DIR / f"{DEFAULT_LANGUAGE}.json"
        
        if not default_file.exists():
            # Create default English language file with basic translations
            default_strings = {
                "common": {
                    "app_title": "Faculty Conference Travel System",
                    "login": "Login",
                    "logout": "Logout",
                    "submit": "Submit",
                    "cancel": "Cancel",
                    "save": "Save",
                    "edit": "Edit",
                    "delete": "Delete",
                    "search": "Search",
                    "filter": "Filter",
                    "loading": "Loading...",
                    "page": "Page",
                    "of": "of",
                    "next": "Next",
                    "previous": "Previous",
                    "yes": "Yes",
                    "no": "No",
                    "success": "Success",
                    "error": "Error",
                    "warning": "Warning",
                    "info": "Information"
                },
                "login": {
                    "title": "Login to Faculty Conference Travel System",
                    "user_id": "User ID",
                    "password": "Password",
                    "login_button": "Login",
                    "error_message": "Invalid credentials. Please try again."
                },
                "professor": {
                    "submit_request": "Submit Request",
                    "my_requests": "My Requests",
                    "conference_info": "Conference Information",
                    "conference_name": "Conference Name",
                    "conference_url": "Conference URL",
                    "destination": "Destination",
                    "city": "City",
                    "date_from": "From Date",
                    "date_to": "To Date",
                    "purpose": "Purpose of Attending",
                    "upload_documents": "Upload Documents",
                    "request_submitted": "Request submitted successfully",
                    "request_details": "Request Details",
                    "status": "Status"
                },
                "approval": {
                    "pending_requests": "Pending Requests",
                    "approved_requests": "Approved Requests",
                    "rejected_requests": "Rejected Requests",
                    "request_details": "Request Details",
                    "approve": "Approve",
                    "reject": "Reject",
                    "approval_notes": "Approval Notes",
                    "rejection_reason": "Rejection Reason",
                    "submit_decision": "Submit Decision",
                    "approved_success": "Request approved successfully",
                    "rejected_success": "Request rejected successfully",
                    "faculty_name": "Faculty Name",
                    "conference_name": "Conference Name",
                    "budget_impact": "Budget Impact"
                },
                "accountant": {
                    "budget_management": "Budget Management",
                    "current_budget": "Current Budget",
                    "add_funds": "Add Funds",
                    "update_budget": "Update Budget",
                    "budget_history": "Budget History",
                    "expense_reports": "Expense Reports",
                    "budget_updated": "Budget updated successfully",
                    "amount": "Amount",
                    "date": "Date",
                    "notes": "Notes",
                    "total_expenses": "Total Expenses",
                    "remaining_budget": "Remaining Budget"
                },
                "admin": {
                    "system_dashboard": "System Dashboard",
                    "feature_flags": "Feature Flags",
                    "performance": "Performance",
                    "accessibility": "Accessibility",
                    "user_activity": "User Activity",
                    "error_monitoring": "Error Monitoring",
                    "configuration": "Configuration"
                }
            }
            
            with open(default_file, 'w', encoding='utf-8') as f:
                json.dump(default_strings, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Created default language file: {default_file}")
        
        # Initialize session state language if not set
        if "language" not in st.session_state:
            st.session_state.language = DEFAULT_LANGUAGE
            
    except Exception as e:
        logging.error(f"Error initializing localization: {str(e)}")

def get_text(key, default=None):
    """
    Get localized text for a given key.
    
    Args:
        key: Dot-notation key (e.g., 'common.submit')
        default: Default value if key not found
        
    Returns:
        str: Localized text
    """
    try:
        current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
        lang_data = load_language_data(current_lang)
        
        # Fall back to default language if current language doesn't have the key
        if current_lang != DEFAULT_LANGUAGE:
            default_lang_data = load_language_data(DEFAULT_LANGUAGE)
        else:
            default_lang_data = {}
        
        # Split key by dots
        parts = key.split(".")
        
        # Navigate through nested dictionaries
        value = lang_data
        for part in parts:
            if part in value:
                value = value[part]
            else:
                # Try default language
                value = default_lang_data
                for default_part in parts:
                    if default_part in value:
                        value = value[default_part]
                    else:
                        # Return provided default or key itself
                        return default if default is not None else key
        
        return value
        
    except Exception as e:
        logging.error(f"Error getting localized text for '{key}': {str(e)}")
        return default if default is not None else key

def t(key, default=None):
    """
    Shorthand function for get_text.
    
    Args:
        key: Dot-notation key (e.g., 'common.submit')
        default: Default value if key not found
        
    Returns:
        str: Localized text
    """
    return get_text(key, default)

def switch_language():
    """
    Display language selector in the UI.
    
    Returns:
        bool: True if language was changed
    """
    current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    
    # Create columns for language selector and info
    cols = st.columns([3, 1])
    
    with cols[1]:
        new_lang = st.selectbox(
            t("common.language", "Language"),
            options=list(AVAILABLE_LANGUAGES.keys()),
            format_func=lambda x: AVAILABLE_LANGUAGES.get(x, x),
            index=list(AVAILABLE_LANGUAGES.keys()).index(current_lang) if current_lang in AVAILABLE_LANGUAGES else 0,
            key="language_selector"
        )
    
    # Check if language changed
    if new_lang != current_lang:
        st.session_state.language = new_lang
        return True
    
    return False

def language_management():
    """Display admin interface for managing translations."""
    st.subheader(t("admin.language_management", "Language Management"))
    
    # Load all languages
    languages = {}
    for lang_code in AVAILABLE_LANGUAGES:
        languages[lang_code] = load_language_data(lang_code)
    
    # Select language to edit
    selected_lang = st.selectbox(
        "Select language to edit",
        options=list(AVAILABLE_LANGUAGES.keys()),
        format_func=lambda x: AVAILABLE_LANGUAGES.get(x, x),
        key="admin_language_selector"
    )
    
    # Load selected language
    lang_data = languages.get(selected_lang, {})
    
    # Create a flattened view of all keys
    flat_keys = {}
    
    def flatten_dict(d, prefix=""):
        for k, v in d.items():
            if isinstance(v, dict):
                flatten_dict(v, f"{prefix}{k}.")
            else:
                flat_keys[f"{prefix}{k}"] = v
    
    # Flatten current language and default language
    flatten_dict(lang_data)
    
    # Default language data for reference
    default_lang_data = languages.get(DEFAULT_LANGUAGE, {})
    default_flat_keys = {}
    flatten_dict(default_lang_data, "")
    
    # Find missing keys
    missing_keys = set(default_flat_keys.keys()) - set(flat_keys.keys())
    
    if missing_keys and selected_lang != DEFAULT_LANGUAGE:
        st.warning(f"This language is missing {len(missing_keys)} translations")
        
        if st.button("Add missing keys"):
            # Add missing keys
            for key in missing_keys:
                parts = key.split(".")
                
                # Navigate and create path in lang_data
                current = lang_data
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set value from default language
                if parts[-1] not in current:
                    current[parts[-1]] = default_flat_keys[key]
            
            # Save updated language file
            lang_file = LOCALE_DIR / f"{selected_lang}.json"
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(lang_data, f, ensure_ascii=False, indent=2)
            
            st.success(f"Added {len(missing_keys)} missing keys")
            st.experimental_rerun()
    
    # Edit translations
    st.subheader("Edit Translations")
    
    # Group by section
    sections = {}
    for key in flat_keys:
        section = key.split(".")[0] if "." in key else "other"
        if section not in sections:
            sections[section] = []
        sections[section].append(key)
    
    # Create tabs for sections
    if sections:
        tabs = st.tabs(list(sections.keys()))
        
        for i, (section, keys) in enumerate(sections.items()):
            with tabs[i]:
                with st.form(f"edit_{section}_{selected_lang}"):
                    changes = {}
                    
                    for key in sorted(keys):
                        # Get current value
                        parts = key.split(".")
                        current_value = flat_keys[key]
                        
                        # Get default language value for reference
                        default_value = default_flat_keys.get(key, "")
                        
                        # Show reference if not default language
                        reference = ""
                        if selected_lang != DEFAULT_LANGUAGE and key in default_flat_keys:
                            reference = f"🇺🇸 {default_value}"
                        
                        # Edit field
                        new_value = st.text_input(
                            f"{key} {reference}",
                            value=current_value,
                            key=f"edit_{selected_lang}_{key}"
                        )
                        
                        # Track changes
                        if new_value != current_value:
                            changes[key] = new_value
                    
                    # Save button
                    if st.form_submit_button("Save Changes"):
                        if changes:
                            # Update lang_data with changes
                            for key, value in changes.items():
                                parts = key.split(".")
                                
                                # Navigate to the right place in the nested dict
                                current = lang_data
                                for part in parts[:-1]:
                                    if part not in current:
                                        current[part] = {}
                                    current = current[part]
                                
                                # Update value
                                current[parts[-1]] = value
                            
                            # Save updated language file
                            lang_file = LOCALE_DIR / f"{selected_lang}.json"
                            with open(lang_file, 'w', encoding='utf-8') as f:
                                json.dump(lang_data, f, ensure_ascii=False, indent=2)
                            
                            st.success(f"Saved {len(changes)} changes")
                            
                            # Clear cache
                            load_language_data.cache_clear()
    else:
        st.info("No translations found for this language. Add the first section.")
    
    # Add new section or key
    st.subheader("Add New Section or Key")
    
    with st.form("add_new_key"):
        new_key = st.text_input("New Key (e.g., professor.new_section.key_name)")
        new_value = st.text_input("Translation")
        
        if st.form_submit_button("Add Key"):
            if new_key and "." in new_key:
                parts = new_key.split(".")
                
                # Navigate and create path in lang_data
                current = lang_data
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set new value
                current[parts[-1]] = new_value
                
                # Save updated language file
                lang_file = LOCALE_DIR / f"{selected_lang}.json"
                with open(lang_file, 'w', encoding='utf-8') as f:
                    json.dump(lang_data, f, ensure_ascii=False, indent=2)
                
                st.success(f"Added new key: {new_key}")
                
                # Clear cache
                load_language_data.cache_clear()
                
                st.experimental_rerun()
            else:
                st.error("Please enter a valid key with at least one section (e.g., common.new_key)")