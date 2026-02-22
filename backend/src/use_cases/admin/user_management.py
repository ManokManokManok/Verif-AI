"""
User Management Use Cases

Use cases for admin user management including listing users,
deleting accounts, resetting passwords, and updating user status/roles.
"""

from typing import Protocol, Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from ...domain.entities import User, UserNotFoundError
from ...domain.admin_entities import (
    AdminActivityLog,
    AdminOperationError,
    UserDeletionError,
    InsufficientPermissionsError,
)


class UserRepository(Protocol):
    """Protocol for user repository."""
    def get_by_id(self, user_id: str) -> Optional[User]: ...
    
    def get_all_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> tuple: ...
    
    def delete_user(self, user_id: str, hard_delete: bool = False) -> bool: ...
    
    def admin_reset_password(self, user_id: str, new_password_hash: str) -> bool: ...
    
    def update_user_status(self, user_id: str, is_active: bool = None, status: str = None) -> bool: ...
    
    def update_user_roles(self, user_id: str, roles: List[str]) -> bool: ...
    
    def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]: ...


class PasswordHasher(Protocol):
    """Protocol for password hashing."""
    def hash_password(self, password: str) -> str: ...


class AdminRepository(Protocol):
    """Protocol for admin audit logging."""
    def log_admin_activity(self, log: AdminActivityLog) -> AdminActivityLog: ...


@dataclass
class ListUsersResult:
    """Result object for list users use case."""
    users: List[User]
    total_count: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success:
            result["data"] = {
                "users": [self._user_to_dict(u) for u in self.users],
                "total": self.total_count,
            }
        else:
            result["error"] = self.error_message
        return result
    
    @staticmethod
    def _user_to_dict(user: User) -> dict:
        """Convert user to dict (excluding sensitive data)."""
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "roles": user.roles,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }


@dataclass
class UserDetailsResult:
    """Result object for get user details use case."""
    user: Optional[User]
    activity_summary: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success and self.user:
            result["data"] = {
                "user": {
                    "id": self.user.id,
                    "email": self.user.email,
                    "username": self.user.username,
                    "roles": self.user.roles,
                    "is_active": self.user.is_active,
                    "is_verified": self.user.is_verified,
                    "created_at": self.user.created_at.isoformat() if self.user.created_at else None,
                    "last_login": self.user.last_login.isoformat() if self.user.last_login else None,
                },
                "activity": self.activity_summary or {},
            }
        else:
            result["error"] = self.error_message
        return result


@dataclass
class OperationResult:
    """Result object for single operations (delete, reset password, etc.)."""
    success: bool
    message: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success:
            result["message"] = self.message
        else:
            result["error"] = self.error_message
        return result


class ListUsersUseCase:
    """
    Use case for listing all users with filtering and pagination.
    
    Supports searching by email/username, filtering by role and status,
    and pagination for large datasets.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize the use case.
        
        Args:
            user_repository: Repository for user data
        """
        self._user_repository = user_repository
    
    def execute(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> ListUsersResult:
        """
        Execute the use case to list users.
        
        Args:
            search: Search term for email/username
            role: Filter by role name
            is_active: Filter by active status
            is_verified: Filter by verification status
            page: Page number (1-indexed)
            page_size: Number of results per page
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            
        Returns:
            ListUsersResult containing users or error
        """
        try:
            # Validate pagination
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 1
            elif page_size > 100:
                page_size = 100
            
            offset = (page - 1) * page_size
            sort_order_int = -1 if sort_order == "desc" else 1
            
            users, total = self._user_repository.get_all_users(
                search=search,
                role=role,
                is_active=is_active,
                is_verified=is_verified,
                limit=page_size,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order_int
            )
            
            return ListUsersResult(
                users=users,
                total_count=total,
                success=True
            )
        except Exception as e:
            return ListUsersResult(
                users=[],
                total_count=0,
                success=False,
                error_message=f"Failed to list users: {str(e)}"
            )


class GetUserDetailsUseCase:
    """
    Use case for getting detailed user information.
    
    Returns user profile data along with activity summary
    (analysis count, last activity, etc.).
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize the use case.
        
        Args:
            user_repository: Repository for user data
        """
        self._user_repository = user_repository
    
    def execute(self, user_id: str) -> UserDetailsResult:
        """
        Execute the use case to get user details.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            UserDetailsResult containing user data or error
        """
        try:
            if not user_id:
                return UserDetailsResult(
                    user=None,
                    activity_summary=None,
                    success=False,
                    error_message="User ID is required"
                )
            
            user = self._user_repository.get_by_id(user_id)
            if not user:
                return UserDetailsResult(
                    user=None,
                    activity_summary=None,
                    success=False,
                    error_message=f"User {user_id} not found"
                )
            
            # Get activity summary
            activity = self._user_repository.get_user_activity_summary(user_id)
            
            return UserDetailsResult(
                user=user,
                activity_summary=activity,
                success=True
            )
        except Exception as e:
            return UserDetailsResult(
                user=None,
                activity_summary=None,
                success=False,
                error_message=f"Failed to get user details: {str(e)}"
            )


class DeleteUserUseCase:
    """
    Use case for deleting a user account.
    
    Supports both soft delete (deactivation) and hard delete (permanent removal).
    Includes protection against deleting admin users and self-deletion.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        admin_repository: Optional[AdminRepository] = None
    ):
        """
        Initialize the use case.
        
        Args:
            user_repository: Repository for user data
            admin_repository: Optional repository for audit logging
        """
        self._user_repository = user_repository
        self._admin_repository = admin_repository
    
    def execute(
        self,
        user_id: str,
        admin_user_id: str,
        hard_delete: bool = False
    ) -> OperationResult:
        """
        Execute the use case to delete a user.
        
        Args:
            user_id: ID of the user to delete
            admin_user_id: ID of the admin performing the action
            hard_delete: If True, permanently delete; if False, soft delete
            
        Returns:
            OperationResult indicating success or failure
        """
        try:
            # Prevent self-deletion
            if user_id == admin_user_id:
                raise UserDeletionError("Cannot delete your own account")
            
            # Get user to check their roles
            user = self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Prevent deletion of super admins
            if "super_admin" in user.roles:
                raise UserDeletionError("Cannot delete super admin accounts")
            
            # Perform deletion
            success = self._user_repository.delete_user(user_id, hard_delete=hard_delete)
            
            if not success:
                raise UserDeletionError("Failed to delete user")
            
            # Log the action
            if self._admin_repository:
                action = "hard_delete_user" if hard_delete else "soft_delete_user"
                log = AdminActivityLog(
                    admin_user_id=admin_user_id,
                    action=action,
                    resource_type="user",
                    resource_id=user_id,
                    details={
                        "user_email": user.email,
                        "hard_delete": hard_delete,
                    }
                )
                self._admin_repository.log_admin_activity(log)
            
            action_text = "permanently deleted" if hard_delete else "deactivated"
            return OperationResult(
                success=True,
                message=f"User {user.email} has been {action_text}"
            )
        except (UserNotFoundError, UserDeletionError) as e:
            return OperationResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"Failed to delete user: {str(e)}"
            )


class AdminResetPasswordUseCase:
    """
    Use case for admin-initiated password reset.
    
    Allows administrators to reset a user's password.
    The user will be required to change password on next login.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        admin_repository: Optional[AdminRepository] = None
    ):
        """
        Initialize the use case.
        
        Args:
            user_repository: Repository for user data
            password_hasher: Service for hashing passwords
            admin_repository: Optional repository for audit logging
        """
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._admin_repository = admin_repository
    
    def execute(
        self,
        user_id: str,
        new_password: str,
        admin_user_id: str
    ) -> OperationResult:
        """
        Execute the use case to reset a user's password.
        
        Args:
            user_id: ID of the user
            new_password: New password (plain text)
            admin_user_id: ID of the admin performing the action
            
        Returns:
            OperationResult indicating success or failure
        """
        try:
            # Validate password length
            if len(new_password) < 8:
                return OperationResult(
                    success=False,
                    error_message="Password must be at least 8 characters"
                )
            
            # Get user
            user = self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Hash the new password
            password_hash = self._password_hasher.hash_password(new_password)
            
            # Update password
            success = self._user_repository.admin_reset_password(user_id, password_hash)
            
            if not success:
                raise AdminOperationError("Failed to reset password")
            
            # Log the action
            if self._admin_repository:
                log = AdminActivityLog(
                    admin_user_id=admin_user_id,
                    action="reset_user_password",
                    resource_type="user",
                    resource_id=user_id,
                    details={"user_email": user.email}
                )
                self._admin_repository.log_admin_activity(log)
            
            return OperationResult(
                success=True,
                message=f"Password reset for {user.email}. User will be required to change password on next login."
            )
        except (UserNotFoundError, AdminOperationError) as e:
            return OperationResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"Failed to reset password: {str(e)}"
            )


class UpdateUserStatusUseCase:
    """
    Use case for updating user account status.
    
    Allows administrators to activate, deactivate, or suspend user accounts.
    Supports both the new `status` string ('active', 'inactive', 'suspended')
    and the legacy `is_active` boolean for backward compatibility.
    """
    
    VALID_STATUSES = {"active", "inactive", "suspended"}
    
    def __init__(
        self,
        user_repository: UserRepository,
        admin_repository: Optional[AdminRepository] = None
    ):
        """
        Initialize the use case.
        
        Args:
            user_repository: Repository for user data
            admin_repository: Optional repository for audit logging
        """
        self._user_repository = user_repository
        self._admin_repository = admin_repository
    
    def execute(
        self,
        user_id: str,
        admin_user_id: str,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> OperationResult:
        """
        Execute the use case to update user status.
        
        Args:
            user_id: ID of the user
            admin_user_id: ID of the admin performing the action
            status: New status string ('active', 'inactive', 'suspended')
            is_active: Legacy boolean active status (deprecated)
            
        Returns:
            OperationResult indicating success or failure
        """
        try:
            # Validate input
            if status is None and is_active is None:
                return OperationResult(
                    success=False,
                    error_message="Either status or is_active must be provided"
                )
            
            # Validate status if provided
            if status is not None:
                status = status.lower()
                if status not in self.VALID_STATUSES:
                    return OperationResult(
                        success=False,
                        error_message=f"Invalid status: {status}. Must be one of {sorted(self.VALID_STATUSES)}"
                    )
            
            # Determine the effective is_active for protection checks
            effective_is_active = (status == "active") if status is not None else is_active
            
            # Prevent self-deactivation/suspension
            if user_id == admin_user_id and not effective_is_active:
                return OperationResult(
                    success=False,
                    error_message="Cannot deactivate or suspend your own account"
                )
            
            # Get user
            user = self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Prevent deactivating/suspending super admins
            if "super_admin" in user.roles and not effective_is_active:
                return OperationResult(
                    success=False,
                    error_message="Cannot deactivate or suspend super admin accounts"
                )
            
            # Update status
            success = self._user_repository.update_user_status(
                user_id,
                is_active=is_active if status is None else None,
                status=status
            )
            
            if not success:
                raise AdminOperationError("Failed to update user status")
            
            # Determine status text for logging and response
            if status is not None:
                status_text = status
                action = f"set_user_{status}"
            else:
                status_text = "activated" if is_active else "deactivated"
                action = "enable_user" if is_active else "disable_user"
            
            # Log the action
            if self._admin_repository:
                log = AdminActivityLog(
                    admin_user_id=admin_user_id,
                    action=action,
                    resource_type="user",
                    resource_id=user_id,
                    details={
                        "user_email": user.email,
                        "new_status": status or ("active" if is_active else "inactive"),
                        "is_active": effective_is_active,
                    }
                )
                self._admin_repository.log_admin_activity(log)
            
            return OperationResult(
                success=True,
                message=f"User {user.email} status has been set to {status_text}"
            )
        except (UserNotFoundError, AdminOperationError) as e:
            return OperationResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"Failed to update user status: {str(e)}"
            )


class UpdateUserRolesUseCase:
    """
    Use case for updating user roles.
    
    Allows administrators to assign or remove roles from users.
    Includes protection against removing admin roles from self.
    """
    
    VALID_ROLES = {"user", "moderator", "admin", "super_admin"}
    
    def __init__(
        self,
        user_repository: UserRepository,
        admin_repository: Optional[AdminRepository] = None
    ):
        """
        Initialize the use case.
        
        Args:
            user_repository: Repository for user data
            admin_repository: Optional repository for audit logging
        """
        self._user_repository = user_repository
        self._admin_repository = admin_repository
    
    def execute(
        self,
        user_id: str,
        roles: List[str],
        admin_user_id: str,
        admin_roles: List[str]
    ) -> OperationResult:
        """
        Execute the use case to update user roles.
        
        Args:
            user_id: ID of the user
            roles: New list of roles
            admin_user_id: ID of the admin performing the action
            admin_roles: Roles of the admin (for permission checking)
            
        Returns:
            OperationResult indicating success or failure
        """
        try:
            # Validate roles
            if not roles:
                return OperationResult(
                    success=False,
                    error_message="At least one role is required"
                )
            
            invalid_roles = set(roles) - self.VALID_ROLES
            if invalid_roles:
                return OperationResult(
                    success=False,
                    error_message=f"Invalid roles: {', '.join(invalid_roles)}"
                )
            
            # Get user
            user = self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Only super_admin can assign super_admin role
            if "super_admin" in roles and "super_admin" not in admin_roles:
                return OperationResult(
                    success=False,
                    error_message="Only super admins can assign super admin role"
                )
            
            # Prevent removing admin role from self
            if user_id == admin_user_id:
                if "admin" in user.roles and "admin" not in roles:
                    return OperationResult(
                        success=False,
                        error_message="Cannot remove admin role from yourself"
                    )
            
            # Store old roles for logging
            old_roles = user.roles.copy() if user.roles else []
            
            # Update roles
            success = self._user_repository.update_user_roles(user_id, roles)
            
            if not success:
                raise AdminOperationError("Failed to update user roles")
            
            # Log the action
            if self._admin_repository:
                log = AdminActivityLog(
                    admin_user_id=admin_user_id,
                    action="update_user_roles",
                    resource_type="user",
                    resource_id=user_id,
                    details={
                        "user_email": user.email,
                        "old_roles": old_roles,
                        "new_roles": roles,
                    }
                )
                self._admin_repository.log_admin_activity(log)
            
            return OperationResult(
                success=True,
                message=f"Roles updated for {user.email}"
            )
        except (UserNotFoundError, AdminOperationError) as e:
            return OperationResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"Failed to update roles: {str(e)}"
            )
