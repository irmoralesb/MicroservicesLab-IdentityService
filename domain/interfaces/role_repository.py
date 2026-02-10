from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel


class RoleRepositoryInterface(ABC):
    """Abstract base class defining the interface for user repository operations."""

    @abstractmethod
    async def get_by_name(self, service_id: UUID, role_name: str) -> RoleModel:
        """Get a role by its name and service id."""
        pass

    @abstractmethod
    async def get_role_list(self, service_id: UUID) -> List[RoleModel]:
        """Get all roles for a service id."""
        pass

    @abstractmethod
    async def create_role(self, role: RoleModel) -> RoleModel:
        """Create a new role assigned to a service id."""
        pass

    @abstractmethod
    async def update_role(self, role: RoleModel) -> RoleModel:
        """Update an existing role."""
        pass

    @abstractmethod
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete a role by id."""
        pass

    @abstractmethod
    async def assign_role(self, user_id: UUID, role_id: UUID) -> bool:
        """Assign a role to a user by ids."""
        pass

    @abstractmethod
    async def unassign_role(self, user_id: UUID, role_id: UUID) -> bool:
        """Unassign a role from a user by ids."""
        pass

    @abstractmethod
    async def get_user_roles(self, user: UserModel) -> List[RoleModel]:
        """Get all roles assigned to a user."""
        pass

    @abstractmethod
    async def check_user_permission(
        self,
        user: UserModel,
        service_id: UUID,
        resource: str,
        action: str,
    ) -> bool:
        """Check whether a user has a permission via roles or direct assignment."""
        pass

    @abstractmethod
    async def get_user_permissions(
        self,
        user: UserModel,
        service_id: UUID | None = None,
    ) -> List[dict]:
        """Get permissions for a user with optional service filtering."""
        pass
