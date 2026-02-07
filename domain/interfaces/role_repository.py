from abc import ABC, abstractmethod
from typing import List

from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel


class RoleRepositoryInterface(ABC):
    """Abstract base class defining the interface for user repository operations."""

    @abstractmethod
    async def get_by_name(self, role_name: str) -> RoleModel:
        """Get a role by its name."""
        pass

    @abstractmethod
    async def assign_role(self, user: UserModel, role: RoleModel) -> bool:
        """Assign a role to a user."""
        pass

    @abstractmethod
    async def get_user_roles(self, user: UserModel) -> List[RoleModel]:
        """Get all roles assigned to a user."""
        pass

    @abstractmethod
    async def check_user_permission(
        self,
        user: UserModel,
        service_name: str,
        resource: str,
        action: str,
    ) -> bool:
        """Check whether a user has a permission via roles or direct assignment."""
        pass

    @abstractmethod
    async def get_user_permissions(
        self,
        user: UserModel,
        service_name: str | None = None,
    ) -> List[dict]:
        """Get permissions for a user with optional service filtering."""
        pass
