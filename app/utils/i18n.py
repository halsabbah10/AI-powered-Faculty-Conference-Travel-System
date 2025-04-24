"""
Internationalization module.
Provides multi-language support for the application.
"""

import os
import json
import streamlit as st
import logging
from functools import lru_cache

# Default language
DEFAULT_LANGUAGE = "en"

# Available languages
AVAILABLE_LANGUAGES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "zh": "中文",
    "ar": "العربية"
}

# Translations directory
TRANSLATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "translations"
)

# Ensure translations directory exists
os.makedirs(TRANSLATIONS_DIR, exist_ok=True)

@lru_cache(maxsize=10)
def load_language_file(lang_code):
    """
    Load language translations from file.
    
    Args:
        lang_code: ISO language code
        
    Returns:
        dict: Translation mapping
    """
    file_path = os.path.join(TRANSLATIONS_DIR, f"{lang_code}.json")
    
    # Create default English file if it doesn't exist
    if lang_code == DEFAULT_LANGUAGE and not os.path.exists(file_path):
        # Default English template
        default_translations = {
            "app_name": "Faculty Conference Travel System",
            "login": {
                "title": "Login",
                "username": "Username",
                "password": "Password",
                "submit": "Login",
                "error": "Invalid username or password"
            },
            "nav": {
                "dashboard": "Dashboard",
                "requests": "My Requests",
                "submit": "Submit Request",
                "approve": "Approval",
                "budget": "Budget",
                "logout": "Logout"
            },
            "professor": {
                "submit_title": "Submit Travel Request",
                "conference_info": "Conference Information",
                "conference_name": "Conference Name",
                "conference_url": "Conference URL",
                "purpose": "Purpose of Attending",
                "destination": "Destination",
                "city": "City",
                "dates": "Travel Dates",
                "date_from": "From",
                "date_to": "To",
                "financial": "Financial Information",
                "registration_fee": "Registration Fee",
                "per_diem": "Per Diem",
                "visa_fee": "Visa Fee",
                "upload_docs": "Upload Documents",
                "conference_doc": "Conference Information Document",
                "paper": "Research Paper",
                "submit_request": "Submit Request",
                "success": "Request submitted successfully",
                "my_requests": "My Requests",
                "status": "Status",
                "details": "Details",
                "no_requests": "No requests found"
            },
            "approval": {
                "pending_title": "Pending Requests",
                "no_pending": "No pending requests",
                "request_details": "Request Details",
                "faculty_info": "Faculty Information",
                "conference_info": "Conference Information",
                "budget_impact": "Budget Impact",
                "document_review": "Document Review",
                "ai_analysis": "AI Analysis",
                "decision": "Decision",
                "approve": "Approve",
                "reject": "Reject",
                "notes": "Notes",
                "submit_decision": "Submit Decision",
                "approved": "Request approved successfully",
                "rejected": "Request rejected successfully"
            },
            "accountant": {
                "budget_title": "Budget Management",
                "current_budget": "Current Budget",
                "update_budget": "Update Budget",
                "amount": "Amount",
                "notes": "Notes",
                "update": "Update Budget",
                "expenses_title": "Expenses",
                "department": "Department",
                "name": "Name",
                "amount": "Amount",
                "date": "Date",
                "reports": "Generate Reports",
                "report_type": "Report Type",
                "date_range": "Date Range",
                "generate": "Generate"
            },
            "common": {
                "loading": "Loading...",
                "error": "An error occurred",
                "success": "Success",
                "warning": "Warning",
                "info": "Information",
                "yes": "Yes",
                "no": "No",
                "save": "Save",
                "cancel": "Cancel",
                "back": "Back",
                "next": "Next",
                "search": "Search",
                "filter": "Filter",
                "sort": "Sort",
                "details": "Details",
                "actions": "Actions",
                "download": "Download",
                "upload": "Upload",
                "preview": "Preview"
            }
        }
        
        # Save default English file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_translations, f, indent=2, ensure_ascii=False)
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # If requested language doesn't exist, fall back to English
            if lang_code != DEFAULT_LANGUAGE:
                logging.warning(f"Language file for '{lang_code}' not found, falling back to {DEFAULT_LANGUAGE}")
                return load_language_file(DEFAULT_LANGUAGE)
            return {}
    except Exception as e:
        logging.error(f"Error loading language file '{lang_code}': {str(e)}")
        return {}

def get_current_language():
    """
    Get current selected language code.
    
    Returns:
        str: Current language code
    """
    if 'language' not in st.session_state:
        # Try to get browser language if available
        try:
            user_lang = None
            if hasattr(st, 'get_user_info'):
                user_info = st.get_user_info()
                user_lang = user_info.get('language', '').split('-')[0]
                
            # Check if browser language is supported
            if user_lang in AVAILABLE_LANGUAGES:
                st.session_state.language = user_lang
            else:
                st.session_state.language = DEFAULT_LANGUAGE
        except:
            st.session_state.language = DEFAULT_LANGUAGE
    
    return st.session_state.language

def set_language(lang_code):
    """
    Set current language.
    
    Args:
        lang_code: ISO language code
    """
    if lang_code in AVAILABLE_LANGUAGES:
        st.session_state.language = lang_code
        # Clear translation cache for session
        if 'translation_cache' in st.session_state:
            del st.session_state.translation_cache

def get_text(key_path, default=None):
    """
    Get translated text for a given key path.
    
    Args:
        key_path: Dot-separated path to translation key
        default: Default text if translation not found
        
    Returns:
        str: Translated text
    """
    lang = get_current_language()
    
    # Check if we have a session cache
    if 'translation_cache' not in st.session_state:
        st.session_state.translation_cache = {}
    
    # Check if this language is in the cache
    if lang not in st.session_state.translation_cache:
        st.session_state.translation_cache[lang] = load_language_file(lang)
    
    translations = st.session_state.translation_cache[lang]
    
    # Navigate through the nested dictionary using the key path
    keys = key_path.split('.')
    value = translations
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        # If key not found in requested language, try English
        if lang != DEFAULT_LANGUAGE:
            try:
                en_translations = st.session_state.translation_cache.get(
                    DEFAULT_LANGUAGE, 
                    load_language_file(DEFAULT_LANGUAGE)
                )
                value = en_translations
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                pass
        
        # Return default or key if not found
        return default if default is not None else key_path

def show_language_selector():
    """Display language selector widget."""
    current_lang = get_current_language()
    
    # Create language selector
    selected_lang = st.selectbox(
        "Language / Idioma / Langue / 语言 / اللغة",
        options=list(AVAILABLE_LANGUAGES.keys()),
        format_func=lambda x: AVAILABLE_LANGUAGES[x],
        index=list(AVAILABLE_LANGUAGES.keys()).index(current_lang)
    )
    
    # Update language if changed
    if selected_lang != current_lang:
        set_language(selected_lang)
        st.experimental_rerun()

def generate_sample_translations():
    """Generate sample translation files for all supported languages."""
    
    # Load English as template
    en_translations = load_language_file(DEFAULT_LANGUAGE)
    
    # Create samples for other languages
    samples = {
        "es": {
            "app_name": "Sistema de Viajes a Conferencias",
            "login": {
                "title": "Iniciar Sesión",
                "username": "Usuario",
                "password": "Contraseña",
                "submit": "Ingresar",
                "error": "Usuario o contraseña inválidos"
            },
            # Add more Spanish translations...
        },
        "fr": {
            "app_name": "Système de Voyage pour Conférences",
            "login": {
                "title": "Connexion",
                "username": "Nom d'utilisateur",
                "password": "Mot de passe",
                "submit": "Connexion",
                "error": "Nom d'utilisateur ou mot de passe invalide"
            },
            # Add more French translations...
        },
        # Add Chinese and Arabic sample translations...
    }
    
    # Save sample files
    for lang_code, translations in samples.items():
        file_path = os.path.join(TRANSLATIONS_DIR, f"{lang_code}.json")
        
        # Only create if file doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
                
    logging.info(f"Generated sample translation files in {TRANSLATIONS_DIR}")