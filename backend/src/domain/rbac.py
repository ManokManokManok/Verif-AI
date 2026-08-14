from typing import List
from .entities import Role


class PermissionChecker:
    def __init__(self, user_roles: List[Role]):
        self.user_roles = user_roles
    
    def can(self, permission: str, resource: str = None) -> bool:
        """
        Check if user has the required permission.
        
        Args:
            permission: The permission to check (e.g., 'create_user')
            resource: Optional resource to check (e.g., 'user')
        
        Returns:
            True if user has permission, False otherwise
        """
        for role in self.user_roles:
            if permission in role.permissions:
                return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role_name: The role name to check (e.g., 'admin')
        
        Returns:
            True if user has the role, False otherwise
        """
        return any(role.name == role_name for role in self.user_roles)
    
    def get_permissions(self) -> List[str]:
        """
        Get all permissions for the user.
        
        Returns:
            List of all unique permissions from all user roles
        """
        all_permissions = []
        for role in self.user_roles:
            all_permissions.extend(role.permissions)
        return list(set(all_permissions))
    
    def get_role_names(self) -> List[str]:
        """
        Get all role names for the user.
        
        Returns:
            List of role names
        """
        return [role.name for role in self.user_roles]
