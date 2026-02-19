from domain.interfaces.service_repository import ServiceRepositoryInterface
from domain.entities.service_model import ServiceModel
from domain.entities.user_service_model import UserServiceModel
from domain.exceptions.services_errors import (
    ServiceCreationError,
    ServiceUpdateError,
    ServiceNotFoundError,
    ServiceDataAccessError,
    AssignServiceToUserError,
    UnassignServiceFromUserError)
from infrastructure.databases.models import ServiceDataModel, UserServicesDataModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import uuid
from core.datetime_utils import parse_mssql_datetime as _parse_mssql_datetime


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
            raise ServiceDataAccessError() from e

    async def get_by_id(self, service_id: uuid.UUID) -> ServiceModel | None:
        try:
            get_by_id_stmt = select(ServiceDataModel).where(
                ServiceDataModel.id == service_id
            )
            result = await self.db.execute(get_by_id_stmt)
            service_datamodel = result.scalars().first()
            return None if service_datamodel is None else self._to_domain(service_datamodel)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceDataAccessError() from e

    async def get_by_name(self, service_name: str) -> ServiceModel | None:
        try:
            get_by_name_stmt = select(ServiceDataModel).where(
                ServiceDataModel.name == service_name
            )
            result = await self.db.execute(get_by_name_stmt)
            service_datamodel = result.scalars().first()
            return None if service_datamodel is None else self._to_domain(service_datamodel)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceDataAccessError() from e

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
            raise ServiceUpdateError(service.name) from e

    def _to_user_service_domain(self, db_user_service: UserServicesDataModel) -> UserServiceModel:
        return UserServiceModel(
            id=db_user_service.id,
            user_id=db_user_service.user_id,
            service_id=db_user_service.service_id,
            assigned_at=_parse_mssql_datetime(db_user_service.assigned_at)
        )

    async def assign_service_to_user(self, user_id: uuid.UUID, service_id: uuid.UUID) -> UserServiceModel:
        """Assign a service to a user."""
        if user_id is None:
            raise ValueError(
                "Cannot assign service to user, no user id was provided.")
        if service_id is None:
            raise ValueError(
                "Cannot assign service to user, no service id was provided.")

        try:
            user_service = UserServicesDataModel(
                user_id=user_id,
                service_id=service_id
            )
            self.db.add(user_service)
            await self.db.commit()
            await self.db.refresh(user_service)
            return self._to_user_service_domain(user_service)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise AssignServiceToUserError(user_id=user_id, service_id=service_id) from e

    async def unassign_service_from_user(self, user_id: uuid.UUID, service_id: uuid.UUID) -> bool:
        """Unassign a service from a user."""
        if user_id is None:
            raise ValueError(
                "Cannot unassign service from user, no user id was provided.")
        if service_id is None:
            raise ValueError(
                "Cannot unassign service from user, no service id was provided.")

        try:
            user_service_stmt = select(UserServicesDataModel).where(
                (UserServicesDataModel.user_id == user_id) &
                (UserServicesDataModel.service_id == service_id)
            )
            result = await self.db.execute(user_service_stmt)
            user_service = result.scalars().first()

            if user_service is None:
                return False

            await self.db.delete(user_service)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UnassignServiceFromUserError(user_id=user_id, service_id=service_id) from e

    async def get_user_services(self, user_id: uuid.UUID) -> List[ServiceModel]:
        """Get all services assigned to a user."""
        if user_id is None:
            raise ValueError(
                "Cannot get user services, no user id was provided.")

        try:
            services_stmt = select(ServiceDataModel).join(
                UserServicesDataModel,
                UserServicesDataModel.service_id == ServiceDataModel.id
            ).where(UserServicesDataModel.user_id == user_id)

            result = await self.db.execute(services_stmt)
            services = result.scalars().all()
            return [self._to_domain(service) for service in services]
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceDataAccessError() from e

    async def has_user_service(self, user_id: uuid.UUID, service_id: uuid.UUID) -> bool:
        """Check if a user has a specific service assigned."""
        if user_id is None or service_id is None:
            return False

        try:
            check_stmt = select(UserServicesDataModel).where(
                (UserServicesDataModel.user_id == user_id) &
                (UserServicesDataModel.service_id == service_id)
            )
            result = await self.db.execute(check_stmt)
            return result.scalars().first() is not None
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ServiceDataAccessError() from e
