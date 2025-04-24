"""
Service Locator module.
Provides centralized access to application services.
"""

import logging
from typing import Dict, Any, Type, Optional, TypeVar, Generic, cast
import inspect
from functools import lru_cache

# Type variable for service interfaces
T = TypeVar('T')

class ServiceLocator:
    """
    Service locator pattern implementation.
    Provides centralized access to services with lazy initialization.
    """
    
    # Dictionary of registered services
    _services: Dict[str, Any] = {}
    
    # Dictionary of service factories
    _factories: Dict[str, callable] = {}
    
    # Dictionary of service instances (singletons)
    _instances: Dict[str, Any] = {}
    
    # Dictionary mapping interfaces to implementations
    _interface_map: Dict[Type, Type] = {}
    
    @classmethod
    def register_service(cls, service_class: Type, interface_class: Optional[Type] = None) -> None:
        """
        Register a service class.
        
        Args:
            service_class: The service implementation class
            interface_class: Optional interface class that the service implements
        """
        service_name = service_class.__name__
        cls._services[service_name] = service_class
        
        # Register interface mapping if provided
        if interface_class:
            cls._interface_map[interface_class] = service_class
    
    @classmethod
    def register_factory(cls, service_name: str, factory_func: callable) -> None:
        """
        Register a factory function for creating service instances.
        
        Args:
            service_name: Name of the service
            factory_func: Factory function that creates the service
        """
        cls._factories[service_name] = factory_func
    
    @classmethod
    def get_service(cls, service_name_or_class: Any) -> Any:
        """
        Get a service instance by name or class.
        
        Args:
            service_name_or_class: Service name (str) or class (Type)
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not found
        """
        # Handle case where a class is provided
        if inspect.isclass(service_name_or_class):
            service_class = service_name_or_class
            
            # Check if this is an interface with a mapping
            if service_class in cls._interface_map:
                service_class = cls._interface_map[service_class]
            
            service_name = service_class.__name__
        else:
            service_name = service_name_or_class
        
        # Check if instance already exists
        if service_name in cls._instances:
            return cls._instances[service_name]
        
        # Check if factory exists
        if service_name in cls._factories:
            instance = cls._factories[service_name]()
            cls._instances[service_name] = instance
            return instance
        
        # Check if service class exists
        if service_name in cls._services:
            service_class = cls._services[service_name]
            instance = service_class()
            cls._instances[service_name] = instance
            return instance
        
        # Service not found
        raise ValueError(f"Service not found: {service_name}")
    
    @classmethod
    def get_service_by_interface(cls, interface_class: Type[T]) -> T:
        """
        Get a service by its interface.
        
        Args:
            interface_class: Interface class
            
        Returns:
            Service instance that implements the interface
            
        Raises:
            ValueError: If no implementation is registered for the interface
        """
        if interface_class in cls._interface_map:
            implementation_class = cls._interface_map[interface_class]
            return cls.get_service(implementation_class)
        
        raise ValueError(f"No implementation registered for interface: {interface_class.__name__}")
    
    @classmethod
    def clear_instances(cls) -> None:
        """Clear all service instances (for testing)."""
        cls._instances.clear()
    
    @classmethod
    def reset(cls) -> None:
        """Reset the service locator (for testing)."""
        cls._services.clear()
        cls._factories.clear()
        cls._instances.clear()
        cls._interface_map.clear()


# Initialize service locator with frequently used services
@lru_cache(maxsize=1)
def get_service_locator():
    """
    Get the service locator instance.
    Ensures we only initialize services once per application instance.
    
    Returns:
        ServiceLocator: The service locator
    """
    return ServiceLocator


# Convenience methods for common services

def get_request_repository():
    """Get the request repository."""
    return get_service_locator().get_service('RequestRepository')

def get_user_repository():
    """Get the user repository."""
    return get_service_locator().get_service('UserRepository')

def get_budget_repository():
    """Get the budget repository."""
    return get_service_locator().get_service('BudgetRepository')

def get_document_repository():
    """Get the document repository."""
    return get_service_locator().get_service('DocumentRepository')

def get_ai_service():
    """Get the AI service."""
    return get_service_locator().get_service('AiService')

def get_export_service():
    """Get the export service."""
    return get_service_locator().get_service('ExportService')

def get_notification_service():
    """Get the notification service."""
    return get_service_locator().get_service('NotificationService')