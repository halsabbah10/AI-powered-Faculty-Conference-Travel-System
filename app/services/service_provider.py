"""
Service Provider module.
Provides convenient global access to services.
"""

from app.services.service_locator import ServiceLocator
from typing import TypeVar, Type, Any, Dict, Optional

# Type variable for service interfaces
T = TypeVar('T')

class ServiceProvider:
    """
    Global service provider for convenient access to application services.
    This class offers a simpler interface to the ServiceLocator.
    """
    
    # Cached repository instances
    _repositories: Dict[str, Any] = {}
    
    @staticmethod
    def db_repository(repository_class: Type[T]) -> T:
        """
        Get a database repository instance.
        
        Args:
            repository_class: Repository class to instantiate
            
        Returns:
            Repository instance
        """
        repo_name = repository_class.__name__
        
        # Return cached instance if available
        if repo_name in ServiceProvider._repositories:
            return ServiceProvider._repositories[repo_name]
        
        # Create new instance
        repo = repository_class()
        ServiceProvider._repositories[repo_name] = repo
        return repo
    
    @staticmethod
    def service(service_class_or_name: Any) -> Any:
        """
        Get a service instance.
        
        Args:
            service_class_or_name: Service class or name
            
        Returns:
            Service instance
        """
        return ServiceLocator.get_service(service_class_or_name)
    
    @staticmethod
    def interface(interface_class: Type[T]) -> T:
        """
        Get a service by interface.
        
        Args:
            interface_class: Interface class
            
        Returns:
            Service implementing the interface
        """
        return ServiceLocator.get_service_by_interface(interface_class)