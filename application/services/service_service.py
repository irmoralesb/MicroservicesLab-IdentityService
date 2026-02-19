from infrastructure.repositories.service_repository import ServiceRepository
from domain.entities.service_model import ServiceModel
from domain.entities.user_service_model import UserServiceModel
from domain.exceptions.services_errors import ServiceNotFoundError, ServiceNameNotFoundError
from typing import List
from uuid import UUID


class ServiceService:
    def __init__(self, service_repo: ServiceRepository) -> None:
        self.service_repo = service_repo

    async def get_service(self, service_id: UUID) -> ServiceModel | None:
        if service_id is None:
            return None

        current_svc = await self.service_repo.get_by_id(service_id)

        if current_svc is None:
            raise ServiceNotFoundError(service_id)

        return current_svc

    async def get_service_by_name(self, service_name: str) -> ServiceModel | None:
        if service_name is None:
            return None

        current_svc = await self.service_repo.get_by_name(service_name)
        if current_svc is None:
            raise ServiceNameNotFoundError(service_name)

        return current_svc

    async def get_all_services(self) -> List[ServiceModel]:
        return await self.service_repo.get_all()

    async def create_service(self, service: ServiceModel) -> ServiceModel:
        return await self.service_repo.create_service(service)

    async def assign_service_to_user(self, user_id: UUID, service_id: UUID) -> UserServiceModel:
        """Assign a service to a user."""
        # Verify service exists
        await self.get_service(service_id)
        return await self.service_repo.assign_service_to_user(user_id, service_id)

    async def unassign_service_from_user(self, user_id: UUID, service_id: UUID) -> bool:
        """Unassign a service from a user."""
        return await self.service_repo.unassign_service_from_user(user_id, service_id)

    async def get_user_services(self, user_id: UUID) -> List[ServiceModel]:
        """Get all services assigned to a user."""
        return await self.service_repo.get_user_services(user_id)

    async def has_user_service(self, user_id: UUID, service_id: UUID) -> bool:
        """Check if a user has a specific service assigned."""
        return await self.service_repo.has_user_service(user_id, service_id)
