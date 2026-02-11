from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from domain.entities.permission_model import PermissionModel


class PermissionRepositoryInterface(ABC):
    """Abstract base class defining the interface for permission repository operations."""

    @abstractmethod
    async def get_by_id(self, permission_id: UUID) -> PermissionModel:
        """Get a permission by its ID."""
        pass

    @abstractmethod
    async def get_all_by_service(self, service_id: UUID) -> List[PermissionModel]:
        """Get all permissions for a specific service."""
        pass

    @abstractmethod
    async def create(self, permission: PermissionModel) -> PermissionModel:
        """Create a new permission."""
        pass

    @abstractmethod
    async def update(self, permission: PermissionModel) -> PermissionModel:
        """Update an existing permission."""
        pass

    @abstractmethod
    async def delete(self, permission_id: UUID) -> bool:
        """Delete a permission by ID."""
        pass

    @abstractmethod
    async def get_permissions_for_role(self, role_id: UUID, service_id: UUID) -> List[tuple[PermissionModel, bool]]:
        """
        Get all permissions for a service with assignment status for a specific role.
        Returns list of tuples: (permission, is_assigned)
        """
        pass

    @abstractmethod
    async def assign_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Assign a permission to a role."""
        pass

    @abstractmethod
    async def unassign_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Unassign a permission from a role."""
        pass

    @abstractmethod
    async def is_assigned_to_any_role(self, permission_id: UUID) -> bool:
        """Check if a permission is assigned to any role."""
        pass
