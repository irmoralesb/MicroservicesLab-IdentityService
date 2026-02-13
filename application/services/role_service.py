from typing import List
from uuid import UUID

from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel
from domain.exceptions.roles_errors import UnspecifiedRoleServiceId
from infrastructure.repositories.role_repository import RoleRepository
from application.services.service_service import ServiceService


class RoleService:
    """Service layer for role and permission operations."""

    def __init__(
        self,
        role_repo: RoleRepository,
        service_svc: ServiceService,
    ) -> None:
        """
        Initialize RoleService with its repository dependency.

        Args:
            role_repo: Repository for role data operations
            service_svc: Service service for validating service existence
        """
        self.role_repo = role_repo
        self.service_svc = service_svc

    async def get_role_by_name(self, service_id: UUID, role_name: str) -> RoleModel:
        """
        Get a role by name.

        Args:
            service_id: Service ID to scope the role lookup
            role_name: Role name to search for

        Returns:
            RoleModel: Matching role
        """
        return await self.role_repo.get_by_name(service_id, role_name)

    async def get_role_list(self, service_id: UUID) -> List[RoleModel]:
        """
        Get all roles for a service.

        Args:
            service_id: Service ID to filter roles

        Returns:
            List[RoleModel]: Roles for the service
        """
        # Check if service exists
        await self.service_svc.get_service(service_id)
        return await self.role_repo.get_role_list(service_id)

    async def create_role(self, role: RoleModel) -> RoleModel:
        """
        Create a new role.

        Args:
            role: Role entity to create

        Returns:
            RoleModel: Created role
        """
        if role.service_id is None:
            raise UnspecifiedRoleServiceId(role.name)

        await self.service_svc.get_service(role.service_id)
        return await self.role_repo.create_role(role)

    async def update_role(self, role: RoleModel) -> RoleModel:
        """
        Update an existing role.

        Args:
            role: Role entity with updated data

        Returns:
            RoleModel: Updated role
        """
        return await self.role_repo.update_role(role)

    async def delete_role(self, role_id: UUID) -> bool:
        """
        Delete a role by ID.

        Args:
            role_id: Role ID to delete

        Returns:
            bool: True if deletion succeeded
        """
        return await self.role_repo.delete_role(role_id)

    async def assign_role(self, user_id: UUID, role_id: UUID) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: User ID to assign the role to
            role_id: Role ID to assign

        Returns:
            bool: True if assignment succeeded
        """
        return await self.role_repo.assign_role(user_id, role_id)

    async def unassign_role(self, user_id: UUID, role_id: UUID) -> bool:
        """
        Unassign a role from a user.

        Args:
            user_id: User ID to unassign the role from
            role_id: Role ID to unassign

        Returns:
            bool: True if unassignment succeeded
        """
        return await self.role_repo.unassign_role(user_id, role_id)

    async def get_user_roles(self, user: UserModel) -> List[RoleModel]:
        """
        Get roles assigned to a user.

        Args:
            user: User entity

        Returns:
            List[RoleModel]: Roles assigned to the user
        """
        return await self.role_repo.get_user_roles(user)

    async def check_user_permission(
        self,
        user: UserModel,
        service_name: str,
        resource: str,
        action: str,
    ) -> bool:
        """
        Check whether a user has permission via roles or direct assignment.

        Args:
            user: User entity
            service_name: Microservice name
            resource: Resource type
            action: Action type

        Returns:
            bool: True if user has permission
        """
        return await self.role_repo.check_user_permission(
            user,
            service_name,
            resource,
            action,
        )

    async def get_user_permissions(
        self,
        user: UserModel,
        service_name: str | None = None,
    ) -> List[dict]:
        """
        Get permissions for a user with optional service filtering.

        Args:
            user: User entity
            service_name: Optional service filter

        Returns:
            List[dict]: Permission entries
        """
        return await self.role_repo.get_user_permissions(user, service_name)
