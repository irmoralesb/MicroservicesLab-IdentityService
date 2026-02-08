from domain.interfaces.service_repository import ServiceRepositoryInterface
from domain.entities.service_model import ServiceModel
from domain.exceptions.services_errors import ServiceCreationError, ServiceNotFoundError
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

    def _to_datamodel(self, service_model: ServiceModel) -> ServiceDataModel:
        return ServiceDataModel(
            name=service_model.name,
            description=service_model.description,
            is_active=service_model.is_active,
            url=service_model.url,
            port=service_model.port
        )

    def _copy_data_to_datamodel(self,  service_model: ServiceModel, service_datamodel: ServiceDataModel) -> None:
        service_datamodel.name = service_model.name
        service_datamodel.description = service_model.description
        service_datamodel.url = service_model.url
        service_datamodel.is_active = service_model.is_active
        service_datamodel.port = service_model.port

    async def get_all(self) -> List[ServiceModel]:
        try:
            get_all_services_stmt = select(ServiceDataModel)
            result = await self.db.execute(get_all_services_stmt)
            services_datamodel = result.scalars().all()
            return [self._to_domain(svc) for svc in services_datamodel]
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceNotFoundError(None) from e

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
            raise ServiceNotFoundError(service_id) from e

    async def create_service(self, service: ServiceModel) -> ServiceModel:
        try:
            service_db = self._to_datamodel(service)
            self.db.add(service_db)
            await self.db.commit()
            await self.db.refresh(service_db)

            return self._to_domain(service_db)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceCreationError(service.name) from e

    async def update_service(self, service: ServiceModel) -> ServiceModel:
        try:
            get_by_id_stmt = select(ServiceDataModel).where(
                ServiceDataModel.id == service.id
            )
            result = await self.db.execute(get_by_id_stmt)
            service_db = result.scalars().first()

            if service_db is None:
                raise ServiceNotFoundError(service.id)

            self._copy_data_to_datamodel(service, service_db)
            await self.db.commit()
            await self.db.refresh(service_db)

            return self._to_domain(service_db)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceCreationError(service.name) from e
