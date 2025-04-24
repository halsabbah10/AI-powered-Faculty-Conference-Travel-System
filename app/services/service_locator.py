"""
Service locator module.
Provides centralized access to application services.
"""

import logging
from functools import lru_cache

class ServiceLocator:
    """
    Service locator implementation for managing application dependencies.
    Provides centralized access to services with lazy initialization.
    """
    
    _instances = {}
    _factories = {}
    
    @classmethod
    def register(cls, service_name, factory=None, instance=None):
        """
        Register a service with the locator.
        
        Args:
            service_name: Unique name for the service
            factory: Optional factory function to create the service
            instance: Optional pre-created instance
            
        Returns:
            None
        """
        if instance is not None:
            cls._instances[service_name] = instance
        elif factory is not None:
            cls._factories[service_name] = factory
        else:
            raise ValueError("Either factory or instance must be provided")
    
    @classmethod
    def get(cls, service_name):
        """
        Get a service instance.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Return existing instance if available
        if service_name in cls._instances:
            return cls._instances[service_name]
        
        # Create new instance if factory is available
        if service_name in cls._factories:
            instance = cls._factories[service_name]()
            cls._instances[service_name] = instance
            return instance
        
        # Service not found
        raise KeyError(f"Service '{service_name}' not registered")
    
    @classmethod
    def has(cls, service_name):
        """
        Check if a service is registered.
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if service is registered
        """
        return service_name in cls._instances or service_name in cls._factories
    
    @classmethod
    def reset(cls, service_name=None):
        """
        Reset service instances.
        
        Args:
            service_name: Optional specific service to reset
                          If None, reset all services
            
        Returns:
            None
        """
        if service_name is None:
            # Reset all instances
            cls._instances = {}
        elif service_name in cls._instances:
            # Reset specific instance
            del cls._instances[service_name]
    
    @classmethod
    def register_repositories(cls):
        """Register all repository services."""
        from app.database.repository import (
            RequestRepository, UserRepository, 
            BudgetRepository, DocumentRepository
        )
        
        cls.register('request_repository', lambda: RequestRepository())
        cls.register('user_repository', lambda: UserRepository())
        cls.register('budget_repository', lambda: BudgetRepository())
        cls.register('document_repository', lambda: DocumentRepository())
    
    @classmethod
    def register_services(cls):
        """Register all business services."""
        from app.services.ai_service import AiService
        from app.services.export_service import ExportService
        from app.services.notification_service import NotificationService
        
        cls.register('ai_service', lambda: AiService())
        cls.register('export_service', lambda: ExportService())
        cls.register('notification_service', lambda: NotificationService())
    
    @classmethod
    def initialize(cls):
        """Initialize all core services."""
        cls.register_repositories()
        cls.register_services()
        logging.info("Service locator initialized")


# Initialize service locator with frequently used services
@lru_cache(maxsize=1)
def get_service_locator():
    """
    Get the service locator instance.
    Ensures we only initialize services once per application instance.
    
    Returns:
        ServiceLocator: The service locator
    """
    ServiceLocator.initialize()
    return ServiceLocator


# Convenience methods for common services

def get_request_repository():
    """Get the request repository."""
    return get_service_locator().get('request_repository')

def get_user_repository():
    """Get the user repository."""
    return get_service_locator().get('user_repository')

def get_budget_repository():
    """Get the budget repository."""
    return get_service_locator().get('budget_repository')

def get_document_repository():
    """Get the document repository."""
    return get_service_locator().get('document_repository')

def get_ai_service():
    """Get the AI service."""
    return get_service_locator().get('ai_service')

def get_export_service():
    """Get the export service."""
    return get_service_locator().get('export_service')

def get_notification_service():
    """Get the notification service."""
    return get_service_locator().get('notification_service')