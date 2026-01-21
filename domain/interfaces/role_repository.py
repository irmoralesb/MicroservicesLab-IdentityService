from abc import ABC, abstractmethod
from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel


class RoleRepositoryInterface(ABC):
    """Abstract base class defining the interface for user repository operations."""

    @abstractmethod
    async def get_by_name(self, role_name: str) -> RoleModel:
        pass

    @abstractmethod
    async def assign_role(self, user: UserModel, role: RoleModel) -> bool:
        pass
