from typing import List
from uuid import UUID

from domain.entities.permission_model import PermissionModel
from infrastructure.repositories.permission_repository import PermissionRepository
from application.services.service_service import ServiceService


class PermissionService:
    """Service layer for permission operations."""

    def __init__(
        self,
        permission_repo: PermissionRepository,
        service_svc: ServiceService,
    ) -> None:
        """
        Initialize PermissionService with its repository dependency.

        Args:
            permission_repo: Repository for permission data operations
            service_svc: Service service for validating service existence
        """
        self.permission_repo = permission_repo
        self.service_svc = service_svc

    async def get_permission(self, permission_id: UUID) -> PermissionModel:
        """
        Get a permission by ID.

        Args:
            permission_id: Permission ID to retrieve

        Returns:
            PermissionModel: Matching permission
        """
        return await self.permission_repo.get_by_id(permission_id)

    async def list_permissions_by_service(self, service_id: UUID) -> List[PermissionModel]:
        """
        Get all permissions for a service.

        Args:
            service_id: Service ID to filter permissions

        Returns:
            List[PermissionModel]: Permissions for the service
        """
        # Check if service exists
        await self.service_svc.get_service(service_id)
        return await self.permission_repo.get_all_by_service(service_id)

    async def create_permission(self, permission: PermissionModel) -> PermissionModel:
        """
        Create a new permission.

        Args:
            permission: Permission entity to create

        Returns:
            PermissionModel: Created permission
        """
        # Validate service exists
        await self.service_svc.get_service(permission.service_id)
        return await self.permission_repo.create(permission)

    async def update_permission(self, permission: PermissionModel) -> PermissionModel:
        """
        Update an existing permission.

        Args:
            permission: Permission entity with updated data

        Returns:
            PermissionModel: Updated permission
        """
        return await self.permission_repo.update(permission)

    async def delete_permission(self, permission_id: UUID) -> bool:
        """
        Delete a permission by ID.
        Validates that the permission is not assigned to any role before deletion.

        Args:
            permission_id: Permission ID to delete

        Returns:
            bool: True if deletion succeeded
        """
        return await self.permission_repo.delete(permission_id)

    async def get_permissions_for_role(
        self, role_id: UUID, service_id: UUID
    ) -> List[tuple[PermissionModel, bool]]:
        """
        Get all permissions for a service with assignment status for a specific role.

        Args:
            role_id: Role ID to check assignments for
            service_id: Service ID to filter permissions

        Returns:
            List[tuple[PermissionModel, bool]]: List of (permission, is_assigned) tuples
        """
        # Validate service exists
        await self.service_svc.get_service(service_id)
        return await self.permission_repo.get_permissions_for_role(role_id, service_id)

    async def assign_permission_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """
        Assign a permission to a role.

        Args:
            role_id: Role ID to assign the permission to
            permission_id: Permission ID to assign

        Returns:
            bool: True if assignment succeeded
        """
        return await self.permission_repo.assign_to_role(role_id, permission_id)

    async def unassign_permission_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """
        Unassign a permission from a role.

        Args:
            role_id: Role ID to unassign the permission from
            permission_id: Permission ID to unassign

        Returns:
            bool: True if unassignment succeeded
        """
        return await self.permission_repo.unassign_from_role(role_id, permission_id)
