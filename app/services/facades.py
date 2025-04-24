"""
Service facades module.
Provides simplified interfaces for business services.
"""

import logging
from datetime import datetime
from app.services.service_locator import get_service_locator
from app.utils.error_handling import ServiceError, ValidationError, DatabaseError

class RequestFacade:
    """Facade for request-related operations."""
    
    @staticmethod
    def get_user_requests(user_id, status=None):
        """
        Get requests for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            list: Requests for the user
            
        Raises:
            DatabaseError: If database error occurs
        """
        try:
            request_repo = get_service_locator().get('request_repository')
            return request_repo.find_requests_by_user(user_id, status)
        except Exception as e:
            logging.error(f"Error getting user requests: {str(e)}")
            raise DatabaseError(
                f"Could not retrieve requests for user {user_id}",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def get_request_details(request_id):
        """
        Get detailed request information.
        
        Args:
            request_id: Request ID
            
        Returns:
            dict: Request details
            
        Raises:
            DatabaseError: If database error occurs
            ValidationError: If request not found
        """
        try:
            request_repo = get_service_locator().get('request_repository')
            request = request_repo.get_request_with_documents(request_id)
            
            if not request:
                raise ValidationError(
                    f"Request with ID {request_id} not found",
                    field="request_id"
                )
            
            return request
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Error getting request details: {str(e)}")
            raise DatabaseError(
                f"Could not retrieve request {request_id}",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def submit_request(request_data, documents=None):
        """
        Submit a new request.
        
        Args:
            request_data: Request form data
            documents: Optional list of document files
            
        Returns:
            int: New request ID
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database error occurs
        """
        try:
            # Validate request data
            from app.utils.validation import validate_conference_input
            
            is_valid, errors = validate_conference_input(request_data)
            if not is_valid:
                raise ValidationError("Invalid request data", details=errors)
            
            # Calculate total cost
            registration_fee = float(request_data.get('registration_fee', 0) or 0)
            per_diem = float(request_data.get('per_diem', 0) or 0)
            visa_fee = float(request_data.get('visa_fee', 0) or 0)
            total_cost = registration_fee + per_diem + visa_fee
            
            # Prepare request data
            request_repo = get_service_locator().get('request_repository')
            
            insert_data = {
                'user_id': request_data['user_id'],
                'conference_name': request_data['conference_name'],
                'conference_url': request_data['conference_url'],
                'destination': request_data['destination'],
                'city': request_data['city'],
                'date_from': request_data['date_from'],
                'date_to': request_data['date_to'],
                'purpose_of_attending': request_data.get('purpose_of_attending', ''),
                'registration_fee': registration_fee,
                'per_diem': per_diem,
                'visa_fee': visa_fee,
                'total_cost': total_cost,
                'date_created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'pending'
            }
            
            # Insert request
            request_id = request_repo.create(insert_data)
            
            # Upload documents if provided
            if documents and request_id:
                document_repo = get_service_locator().get('document_repository')
                
                for doc in documents:
                    if hasattr(doc, 'read'):
                        doc_data = doc.read()
                        document_repo.add_document(
                            request_id=request_id,
                            file_name=doc.name,
                            file_type=doc.type,
                            file_content=doc_data,
                            description=doc.description if hasattr(doc, 'description') else None
                        )
            
            # Create notification
            notification_service = get_service_locator().get('notification_service')
            notification_service.create_notification(
                user_id=request_data['user_id'],
                message=f"Your travel request for {request_data['conference_name']} has been submitted",
                notification_type="info",
                related_id=str(request_id)
            )
            
            # Notify approvers
            from app.database.repository import UserRepository
            user_repo = UserRepository()
            approvers = user_repo.find_by_role('approval')
            
            for approver in approvers:
                notification_service.create_notification(
                    user_id=approver['user_id'],
                    message=f"New travel request pending approval: {request_data['conference_name']}",
                    notification_type="info",
                    related_id=str(request_id)
                )
            
            return request_id
            
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Error submitting request: {str(e)}")
            raise DatabaseError(
                "Could not submit request",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def update_request_status(request_id, status, notes=None, approver_id=None):
        """
        Update request status.
        
        Args:
            request_id: Request ID
            status: New status
            notes: Optional approval/rejection notes
            approver_id: ID of the approver
            
        Returns:
            bool: Success status
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database error occurs
        """
        try:
            # Validate status
            if status not in ['approved', 'rejected', 'pending']:
                raise ValidationError(
                    f"Invalid status: {status}",
                    field="status"
                )
            
            # Get request details first
            request_repo = get_service_locator().get('request_repository')
            request = request_repo.find_by_id(request_id)
            
            if not request:
                raise ValidationError(
                    f"Request with ID {request_id} not found",
                    field="request_id"
                )
            
            # Update status
            success = request_repo.update_request_status(
                request_id=request_id,
                status=status,
                notes=notes,
                approved_by=approver_id
            )
            
            if not success:
                raise DatabaseError(
                    f"Failed to update request {request_id} status",
                    details={"request_id": request_id, "status": status}
                )
            
            # Create notification for user
            notification_service = get_service_locator().get('notification_service')
            
            if status == 'approved':
                notification_service.create_notification(
                    user_id=request['user_id'],
                    message=f"Your travel request for {request['conference_name']} has been approved",
                    notification_type="success",
                    related_id=str(request_id)
                )
            elif status == 'rejected':
                notification_service.create_notification(
                    user_id=request['user_id'],
                    message=f"Your travel request for {request['conference_name']} has been rejected",
                    notification_type="error",
                    related_id=str(request_id),
                    data={"rejection_reason": notes}
                )
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Error updating request status: {str(e)}")
            raise DatabaseError(
                f"Could not update request {request_id} status",
                details={"original_error": str(e)}
            )


class BudgetFacade:
    """Facade for budget-related operations."""
    
    @staticmethod
    def get_budget_summary(department=None):
        """
        Get budget summary.
        
        Args:
            department: Optional department filter
            
        Returns:
            dict: Budget summary
            
        Raises:
            DatabaseError: If database error occurs
        """
        try:
            budget_repo = get_service_locator().get('budget_repository')
            current_budget = budget_repo.get_current_budget(department)
            
            # Get spending statistics
            request_repo = get_service_locator().get('request_repository')
            department_param = department if department else None
            year = datetime.now().year
            
            stats = request_repo.get_request_statistics(department_param, year)
            
            # Calculate remaining budget
            budget_amount = float(current_budget.get('amount', 0))
            remaining = float(current_budget.get('remaining', 0))
            
            # Calculate utilization percentage
            utilization = 0
            if budget_amount > 0:
                utilization = ((budget_amount - remaining) / budget_amount) * 100
            
            return {
                'budget': current_budget,
                'statistics': stats,
                'utilization': utilization
            }
            
        except Exception as e:
            logging.error(f"Error getting budget summary: {str(e)}")
            raise DatabaseError(
                "Could not retrieve budget summary",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def update_budget(budget_data):
        """
        Update budget.
        
        Args:
            budget_data: Budget form data
            
        Returns:
            int: Budget ID
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database error occurs
        """
        try:
            # Validate budget data
            from app.utils.validation import validate_budget_input
            
            is_valid, errors = validate_budget_input(budget_data)
            if not is_valid:
                raise ValidationError("Invalid budget data", details=errors)
            
            budget_repo = get_service_locator().get('budget_repository')
            
            # Check if budget already exists
            existing_budget = None
            
            if 'budget_id' in budget_data and budget_data['budget_id']:
                existing_budget = budget_repo.find_by_id(budget_data['budget_id'])
            
            # Prepare budget data
            insert_data = {
                'department': budget_data['department'],
                'year': int(budget_data['year']),
                'quarter': int(budget_data['quarter']),
                'amount': float(budget_data['amount']),
                'remaining': float(budget_data['amount']),  # Initially set remaining to full amount
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            budget_id = None
            
            if existing_budget:
                # Update existing budget
                budget_repo.update(existing_budget['budget_id'], insert_data)
                budget_id = existing_budget['budget_id']
            else:
                # Create new budget
                budget_id = budget_repo.create(insert_data)
            
            # Create notification for department heads
            notification_service = get_service_locator().get('notification_service')
            
            from app.database.repository import UserRepository
            user_repo = UserRepository()
            department_users = user_repo.find_all(
                where="department = %s",
                params=(budget_data['department'],)
            )
            
            for user in department_users:
                notification_service.create_notification(
                    user_id=user['user_id'],
                    message=f"Budget updated for {budget_data['department']} department: ${float(budget_data['amount']):,.2f}",
                    notification_type="info"
                )
            
            return budget_id
            
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Error updating budget: {str(e)}")
            raise DatabaseError(
                "Could not update budget",
                details={"original_error": str(e)}
            )


class UserFacade:
    """Facade for user-related operations."""
    
    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate user login.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            dict: User data if successful, None otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if not username or not password:
                raise ValidationError(
                    "Username and password are required",
                    details={"username": "Username is required", "password": "Password is required"}
                )
            
            user_repo = get_service_locator().get('user_repository')
            user = user_repo.authenticate(username, password)
            
            if not user:
                raise ValidationError(
                    "Invalid username or password",
                    details={"auth": "Invalid username or password"}
                )
            
            return user
            
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Error authenticating user: {str(e)}")
            raise ServiceError(
                "Authentication service unavailable",
                service="auth",
                operation="login"
            )
    
    @staticmethod
    def get_user_profile(user_id):
        """
        Get user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            dict: User profile
            
        Raises:
            ValidationError: If user not found
            DatabaseError: If database error occurs
        """
        try:
            user_repo = get_service_locator().get('user_repository')
            user = user_repo.find_by_id(user_id)
            
            if not user:
                raise ValidationError(
                    f"User with ID {user_id} not found",
                    field="user_id"
                )
            
            # Remove sensitive information
            if 'password' in user:
                del user['password']
            
            return user
            
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Error getting user profile: {str(e)}")
            raise DatabaseError(
                f"Could not retrieve user {user_id} profile",
                details={"original_error": str(e)}
            )