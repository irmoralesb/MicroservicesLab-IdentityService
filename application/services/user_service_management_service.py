from uuid import UUID
from typing import List

from domain.entities.service_model import ServiceModel
from domain.entities.user_service_model import UserServiceModel
from application.services.service_service import ServiceService
from application.services.role_service import RoleService


class UserServiceManagementService:
    """
    Orchestrator service for managing user-service relationships.
    
    This service coordinates between ServiceService and RoleService to maintain
    data consistency when assigning/unassigning services to users.
    """

    def __init__(
        self,
        service_svc: ServiceService,
        role_svc: RoleService,
    ) -> None:
        self.service_svc = service_svc
        self.role_svc = role_svc

    async def assign_service_to_user(
        self, user_id: UUID, service_id: UUID
    ) -> UserServiceModel:
        """
        Assign a service to a user.

        Args:
            user_id: User ID to assign the service to
            service_id: Service ID to assign

        Returns:
            UserServiceModel: The created user-service assignment
        """
        return await self.service_svc.assign_service_to_user(user_id, service_id)

    async def unassign_service_from_user(
        self, user_id: UUID, service_id: UUID
    ) -> bool:
        """
        Unassign a service from a user and remove all associated service roles.

        This method ensures data consistency by:
        1. First removing all roles belonging to this service from the user
        2. Then removing the service assignment itself

        Args:
            user_id: User ID to unassign the service from
            service_id: Service ID to unassign

        Returns:
            bool: True if the service was unassigned, False if not found
        """
        # First, remove all roles for this service from the user
        await self.role_svc.unassign_service_roles_from_user(user_id, service_id)

        # Then, unassign the service itself
        return await self.service_svc.unassign_service_from_user(user_id, service_id)

    async def get_user_services(self, user_id: UUID) -> List[ServiceModel]:
        """
        Get all services assigned to a user.

        Args:
            user_id: User ID to get services for

        Returns:
            List[ServiceModel]: List of services assigned to the user
        """
        return await self.service_svc.get_user_services(user_id)

    async def has_user_service(self, user_id: UUID, service_id: UUID) -> bool:
        """
        Check if a user has a specific service assigned.

        Args:
            user_id: User ID to check
            service_id: Service ID to check

        Returns:
            bool: True if the user has the service assigned
        """
        return await self.service_svc.has_user_service(user_id, service_id)
