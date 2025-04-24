"""
Service interfaces module.
Defines interfaces for application services to ensure consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

class RepositoryInterface(ABC):
    """Abstract interface for repositories."""
    
    @abstractmethod
    def find_by_id(self, id_value):
        """Find an entity by ID."""
        pass
    
    @abstractmethod
    def find_all(self, where=None, params=None, order_by=None, limit=None, offset=None):
        """Find all entities matching criteria."""
        pass
    
    @abstractmethod
    def create(self, data):
        """Create a new entity."""
        pass
    
    @abstractmethod
    def update(self, id_value, data):
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id_value):
        """Delete an entity."""
        pass

class NotificationServiceInterface(ABC):
    """Abstract interface for notification service."""
    
    @abstractmethod
    def create_notification(self, user_id, message, notification_type="info", related_id=None, data=None):
        """Create a new notification."""
        pass
    
    @abstractmethod
    def get_notifications(self, user_id, include_read=False, limit=20):
        """Get notifications for a user."""
        pass
    
    @abstractmethod
    def mark_as_read(self, user_id, notification_id=None):
        """Mark notifications as read."""
        pass
    
    @abstractmethod
    def delete_notification(self, user_id, notification_id):
        """Delete a notification."""
        pass

class AIServiceInterface(ABC):
    """Abstract interface for AI service."""
    
    @abstractmethod
    def analyze_text(self, text, analysis_type, options=None):
        """Analyze text using AI."""
        pass
    
    @abstractmethod
    def generate_text(self, prompt, options=None):
        """Generate text using AI."""
        pass
    
    @abstractmethod
    def validate_content(self, content, validation_type, options=None):
        """Validate content using AI."""
        pass
    
    @abstractmethod
    def get_recommendations(self, context, options=None):
        """Get recommendations based on context."""
        pass

class FeatureFlagServiceInterface(ABC):
    """Abstract interface for feature flag service."""
    
    @abstractmethod
    def is_enabled(self, feature_name, user_role=None):
        """Check if a feature is enabled."""
        pass
    
    @abstractmethod
    def get_all_flags(self):
        """Get all feature flags."""
        pass
    
    @abstractmethod
    def update_flag(self, feature_name, enabled=None, description=None, roles=None):
        """Update a feature flag."""
        pass