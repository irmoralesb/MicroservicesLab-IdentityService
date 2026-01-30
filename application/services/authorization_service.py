from typing import List
from domain.entities.user_model import UserWithRolesModel
from domain.exceptions.auth_exceptions import MissingPermissionException, MissingRoleException
from infrastructure.repositories.role_repository import RoleRepository
from core.settings import app_settings


class AuthorizationService:
    """Service for handling authorization checks with service-scoped permissions"""
    
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo
        self.service_name = app_settings.service_name
    
    async def check_permission(
        self, 
        user: UserWithRolesModel, 
        resource: str, 
        action: str
    ) -> bool:
        """
        Check if user has permission to perform action on resource
        within THIS microservice context
        
        Args:
            user: User with roles
            resource: Resource type (e.g., 'user', 'role')
            action: Action type (e.g., 'create', 'read', 'update', 'delete')
            
        Returns:
            bool: True if user has permission
            
        Raises:
            MissingPermissionException: If user lacks required permission
        """
        # Check permission with service scope
        has_permission = await self.role_repo.check_user_permission(
            user.user,
            self.service_name,
            resource, 
            action
        )
        
        if not has_permission:
            raise MissingPermissionException(resource, action)
        
        return True
    
    async def check_permission_for_service(
        self,
        user: UserWithRolesModel,
        service_name: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user has permission for a SPECIFIC service
        Useful for cross-service authorization checks
        
        Args:
            user: User with roles
            service_name: Target service name
            resource: Resource type
            action: Action type
            
        Returns:
            bool: True if user has permission
            
        Raises:
            MissingPermissionException: If user lacks required permission
        """
        has_permission = await self.role_repo.check_user_permission(
            user.user,
            service_name,
            resource,
            action
        )
        
        if not has_permission:
            raise MissingPermissionException(resource, action)
        
        return True
    
    def check_role(
        self, 
        user: UserWithRolesModel, 
        role_name: str,
        service_name: str | None = None
    ) -> bool:
        """
        Check if user has specific role
        
        Args:
            user: User with roles
            role_name: Name of role to check
            service_name: Optional service filter. If None, checks current service
            
        Returns:
            bool: True if user has role
            
        Raises:
            MissingRoleException: If user lacks required role
        """
        target_service = service_name or self.service_name
        
        # Filter roles by service and name
        matching_roles = [
            role for role in user.roles 
            if role.service == target_service and role.name == role_name
        ]
        
        if not matching_roles:
            raise MissingRoleException(role_name)
        
        return True
    
    async def get_user_permissions_for_service(
        self,
        user: UserWithRolesModel,
        service_name: str | None = None
    ) -> List[dict]:
        """
        Get all user permissions for a specific service
        
        Args:
            user: User with roles
            service_name: Service name (defaults to current service)
            
        Returns:
            List of permission dictionaries
        """
        target_service = service_name or self.service_name
        return await self.role_repo.get_user_permissions(
            user.user, 
            target_service
        )