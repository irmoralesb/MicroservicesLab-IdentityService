from domain.interfaces.service_repository import ServiceRepositoryInterface
from domain.entities.service_model import ServiceModel
from domain.exceptions.services_errors import ServiceNotFoundException
from infrastructure.databases.models import ServiceDataModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import uuid


class ServiceRepository(ServiceRepositoryInterface):

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        super().__init__()

    def _to_domain(self, db_service: ServiceDataModel) -> ServiceModel:
        return ServiceModel(
            id=db_service.id,
            name=db_service.name,
            description=db_service.description,
            url=db_service.url,
            port=db_service.port,
            is_active=db_service.is_active
        )

    async def get_all(self) -> List[ServiceModel]:
        try:
            get_all_services_stmt = select(ServiceDataModel)
            result = await self.db.execute(get_all_services_stmt)
            services_datamodel = result.scalars().all()
            return [self._to_domain(svc) for svc in services_datamodel]
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceNotFoundException("") from e

    async def get_by_id(self, service_id: uuid.UUID) -> ServiceModel | None:
        try:
            get_by_id_stmt = select(ServiceDataModel).where(
                ServiceDataModel.id == service_id
            )
            result = await self.db.execute(get_by_id_stmt)
            service_datamodel = result.scalars().first()
            return None if service_datamodel == None else self._to_domain(service_datamodel)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceNotFoundException("") from e
