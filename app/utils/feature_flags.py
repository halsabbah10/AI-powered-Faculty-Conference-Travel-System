"""
Feature flags module.
Provides functionality for controlling feature enablement.
"""

import os
import json
import logging
from datetime import datetime
import streamlit as st

# Default feature flag location
FLAG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "feature_flags.json"
)

# Ensure config directory exists
os.makedirs(os.path.dirname(FLAG_FILE), exist_ok=True)

class FeatureFlags:
    """Feature flag management system."""
    
    _flags = None
    
    @classmethod
    def _load_flags(cls):
        """Load feature flags from configuration."""
        if cls._flags is not None:
            return cls._flags
            
        try:
            if os.path.exists(FLAG_FILE):
                with open(FLAG_FILE, 'r') as f:
                    cls._flags = json.load(f)
            else:
                # Create default flag file
                cls._flags = {
                    "features": {
                        "ai_analysis": {
                            "enabled": True,
                            "description": "AI-powered analysis of research papers and conferences",
                            "roles": ["professor", "approval"]
                        },
                        "budget_forecasting": {
                            "enabled": True,
                            "description": "Budget forecasting and trend analysis",
                            "roles": ["accountant", "approval"]
                        },
                        "email_notifications": {
                            "enabled": False,
                            "description": "Email notifications for status changes",
                            "roles": ["all"]
                        },
                        "enhanced_reporting": {
                            "enabled": True,
                            "description": "Enhanced PDF report generation",
                            "roles": ["accountant", "approval"]
                        },
                        "feedback_system": {
                            "enabled": True,
                            "description": "User feedback collection and analysis",
                            "roles": ["all"]
                        }
                    },
                    "updated_at": datetime.now().isoformat()
                }
                
                # Save default flags
                with open(FLAG_FILE, 'w') as f:
                    json.dump(cls._flags, f, indent=2)
                    
        except Exception as e:
            logging.error(f"Error loading feature flags: {str(e)}")
            # Fallback to defaults
            cls._flags = {
                "features": {},
                "updated_at": datetime.now().isoformat()
            }
            
        return cls._flags
    
    @classmethod
    def is_enabled(cls, feature_name, user_role=None):
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature to check
            user_role: Optional user role for role-specific features
            
        Returns:
            bool: True if feature is enabled, False otherwise
        """
        flags = cls._load_flags()
        
        # Check if feature exists
        if feature_name not in flags["features"]:
            logging.warning(f"Feature flag '{feature_name}' not found")
            return False
            
        feature = flags["features"][feature_name]
        
        # Check if feature is enabled
        if not feature.get("enabled", False):
            return False
            
        # Check role restrictions if role provided
        if user_role and "roles" in feature:
            roles = feature["roles"]
            if "all" not in roles and user_role not in roles:
                return False
                
        return True
    
    @classmethod
    def get_all_flags(cls):
        """
        Get all feature flags.
        
        Returns:
            dict: Feature flag data
        """
        return cls._load_flags()
    
    @classmethod
    def update_flag(cls, feature_name, enabled=None, description=None, roles=None):
        """
        Update a feature flag.
        
        Args:
            feature_name: Name of the feature to update
            enabled: Optional new enabled status
            description: Optional new description
            roles: Optional new role restrictions
            
        Returns:
            bool: Success status
        """
        try:
            flags = cls._load_flags()
            
            # Create feature if it doesn't exist
            if feature_name not in flags["features"]:
                flags["features"][feature_name] = {
                    "enabled": False,
                    "description": "",
                    "roles": ["all"]
                }
                
            feature = flags["features"][feature_name]
            
            # Update fields
            if enabled is not None:
                feature["enabled"] = enabled
                
            if description is not None:
                feature["description"] = description
                
            if roles is not None:
                feature["roles"] = roles
                
            # Update timestamp
            flags["updated_at"] = datetime.now().isoformat()
            
            # Save changes
            with open(FLAG_FILE, 'w') as f:
                json.dump(flags, f, indent=2)
                
            # Reset cached flags
            cls._flags = None
            
            logging.info(f"Feature flag '{feature_name}' updated")
            return True
            
        except Exception as e:
            logging.error(f"Error updating feature flag: {str(e)}")
            return False

def show_feature_flags_manager():
    """Show admin interface for managing feature flags."""
    st.subheader("Feature Flags Management")
    
    # Get all flags
    flags = FeatureFlags.get_all_flags()
    
    # Display last update time
    if "updated_at" in flags:
        st.info(f"Last updated: {flags['updated_at']}")
    
    # Edit existing flags
    st.subheader("Existing Flags")
    
    for feature_name, feature in flags.get("features", {}).items():
        with st.expander(f"{feature_name}: {'Enabled' if feature.get('enabled', False) else 'Disabled'}"):
            enabled = st.toggle(
                "Enabled",
                value=feature.get("enabled", False),
                key=f"toggle_{feature_name}"
            )
            
            description = st.text_input(
                "Description",
                value=feature.get("description", ""),
                key=f"desc_{feature_name}"
            )
            
            all_roles = ["professor", "accountant", "approval", "admin", "all"]
            current_roles = feature.get("roles", ["all"])
            
            roles = st.multiselect(
                "Allowed Roles",
                options=all_roles,
                default=current_roles,
                key=f"roles_{feature_name}"
            )
            
            if st.button("Update", key=f"update_{feature_name}"):
                success = FeatureFlags.update_flag(
                    feature_name,
                    enabled=enabled,
                    description=description,
                    roles=roles
                )
                
                if success:
                    st.success(f"Feature flag '{feature_name}' updated successfully")
                else:
                    st.error(f"Failed to update feature flag '{feature_name}'")
    
    # Add new flag
    st.subheader("Add New Feature Flag")
    
    with st.form("new_feature_flag"):
        new_name = st.text_input("Feature Name")
        new_enabled = st.toggle("Enabled", value=False)
        new_description = st.text_input("Description")
        new_roles = st.multiselect(
            "Allowed Roles",
            options=["professor", "accountant", "approval", "admin", "all"],
            default=["all"]
        )
        
        submit = st.form_submit_button("Add Feature Flag")
        
        if submit and new_name:
            success = FeatureFlags.update_flag(
                new_name,
                enabled=new_enabled,
                description=new_description,
                roles=new_roles
            )
            
            if success:
                st.success(f"Feature flag '{new_name}' created successfully")
            else:
                st.error(f"Failed to create feature flag '{new_name}'")