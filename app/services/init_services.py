"""
Service initialization module.
Registers and configures all application services.
"""

import logging
from app.services.service_locator import ServiceLocator
from app.services.ai_service import AIService
from app.services.notification_service import NotificationService
from app.database.repository import (
    UserRepository, RequestRepository, 
    DocumentRepository, BudgetRepository
)

def init_services():
    """Initialize and register all application services."""
    try:
        logging.info("Initializing application services...")
        
        # Register repositories
        ServiceLocator.register_service(UserRepository)
        ServiceLocator.register_service(RequestRepository)
        ServiceLocator.register_service(DocumentRepository)
        ServiceLocator.register_service(BudgetRepository)
        
        # Register services
        ServiceLocator.register_service(AIService)
        ServiceLocator.register_service(NotificationService)
        
        # Register facades and other services
        from app.services.budget_facade import BudgetFacade
        ServiceLocator.register_service(BudgetFacade)
        
        # Register any service with factory methods
        from app.utils.feature_flags import FeatureFlagService
        ServiceLocator.register_factory("FeatureFlagService", FeatureFlagService.get_instance)
        
        logging.info("Application services initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing services: {str(e)}")
        raise