from infrastructure.repositories.service_repository import ServiceRepository
from domain.entities.service_model import ServiceModel
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
