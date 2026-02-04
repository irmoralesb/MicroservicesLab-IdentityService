from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.entities.user_model import UserModel
from infrastructure.databases.models import UserDataModel
from domain.exceptions.auth_errors import (
    UserAlreadyExistsError,
    UserCreationError,
    UserNotFoundError,
    UserUpdateError,
    UserDeleteError)
from domain.interfaces.user_repository import UserRepositoryInterface
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime
import re
from infrastructure.observability.metrics.decorators import track_database_operation

_DATETIMEOFFSET_RE = re.compile(
    r"^(?P<base>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<frac>\d{1,7}))? (?P<tz>[+-]\d{2}:\d{2})$"
)

def _parse_mssql_datetime(value: datetime | str | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    match = _DATETIMEOFFSET_RE.match(value)
    if not match:
        return datetime.fromisoformat(value)
    frac = (match.group("frac") or "0").ljust(6, "0")[:6]
    normalized = f"{match.group('base')}.{frac}{match.group('tz')}"
    return datetime.fromisoformat(normalized)


class UserRepository(UserRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_domain(self, db_user: UserDataModel) -> UserModel:
        return UserModel(
            id=db_user.id,
            first_name=db_user.first_name,
            middle_name=db_user.middle_name,
            last_name=db_user.last_name,
            email=db_user.email,
            created_at=_parse_mssql_datetime(db_user.created_at),
            updated_at=_parse_mssql_datetime(db_user.updated_at),
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            hashed_password=db_user.hashed_password,
            failed_login_attempts=db_user.failed_login_attempts,
            locked_until=db_user.locked_until
        )

    def _to_datamodel(self, user: UserModel) -> UserDataModel:
        return UserDataModel(
            id=user.id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            is_verified=user.is_verified,
            hashed_password=user.hashed_password,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until
        )

    def _update_datamodel(self, user: UserModel, user_data: UserDataModel) -> None:
        """It updates the user data model with data from the user model"""
        user_data.first_name = user.first_name
        user_data.middle_name = user.middle_name
        user_data.last_name = user.last_name
        user_data.email = user.email
        user_data.is_active = user.is_active
        user_data.is_verified = user.is_verified
        user_data.failed_login_attempts = user.failed_login_attempts
        user_data.locked_until = user.locked_until
        user_data.hashed_password = user.hashed_password


    @track_database_operation(operation_type='insert', table='users')
    async def create_user(self, user: UserModel) -> UserModel:
        """Add a new user"""
        if user is None:
            raise ValueError("Cannot create user, no data was provided.")

        user_exists = await self.exists_by_email(user.email)

        if user_exists:
            raise UserAlreadyExistsError(user.email)

        try:
            create_user_model = self._to_datamodel(user)
            self.db.add(create_user_model)
            await self.db.commit()
            await self.db.refresh(create_user_model)

            return self._to_domain(create_user_model)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserCreationError(user.email) from e

    @track_database_operation(operation_type='update', table='users')
    async def update_user(self, user: UserModel) -> UserModel:
        """Update existing user"""

        if user is None or user.id is None:
            raise UserNotFoundError(user.email)

        try:
            get_user_to_update_stmt = select(UserDataModel).where(
                UserDataModel.id == user.id
            )
            result = await self.db.execute(get_user_to_update_stmt)
            user_to_update = result.scalars().first()

            if user_to_update is None:
                raise UserNotFoundError(user.email)
            self._update_datamodel(user, user_to_update)
            await self.db.commit()
            await self.db.refresh(user_to_update)
            return self._to_domain(user_to_update)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserUpdateError(user.email) from e


    @track_database_operation(operation_type='delete', table='users')
    async def soft_delete_user(self, user: UserModel) -> bool:
        """Soft delete user"""
        if user is None or user.id is None:
            raise UserNotFoundError(user.email)
        
        try:
            get_user_to_update_stmt = select(UserDataModel).where(
                UserDataModel.id == user.id
            )
            result = await self.db.execute(get_user_to_update_stmt)
            user_to_update = result.scalars().first()

            if user_to_update is None:
                raise UserNotFoundError(user.email)

            self._update_datamodel(user, user_to_update)
            user_to_update.is_deleted = True
            await self.db.commit()
            await self.db.refresh(user_to_update)
            return True
        except SQLAlchemyError as e:
            raise UserDeleteError(user.email) from e


    @track_database_operation(operation_type='select', table='users')
    async def get_by_email(self, email: str) -> UserModel | None:
        """Get user by email"""
        try:
            check_user_email_stmt = select(UserDataModel).where(
                (UserDataModel.email == email) & (UserDataModel.is_deleted == False)
            )
            result = await self.db.execute(check_user_email_stmt)
            existing_user = result.scalars().first()

            return None if existing_user is None else self._to_domain(existing_user)
        except SQLAlchemyError as e:
            raise UserNotFoundError(email) from e

    @track_database_operation(operation_type='select', table='users')
    async def get_by_id(self, id: UUID) -> UserModel | None:
        """Get user by id"""
        try:
            get_user_stmt = select(UserDataModel).where(
                UserDataModel.id == id
            )
            result = await self.db.execute(get_user_stmt)
            exiting_user = result.scalars().first()
            return None if exiting_user is None else self._to_domain(exiting_user)
        except SQLAlchemyError as e:
            raise UserNotFoundError(str(id)) from e

    async def exists_by_email(self, email: str) -> bool:
        """Check the user exist by email"""
        try:
            check_user_email_stmt = select(UserDataModel).where(
                UserDataModel.email == email)
            result = await self.db.execute(check_user_email_stmt)
            existing_user = result.scalars().first()

            return False if existing_user is None else True
        except SQLAlchemyError as e:
            raise UserNotFoundError(email) from e

    @track_database_operation(operation_type='select', table='users')
    async def get_user_list(self) -> List[UserModel]:
        try:
            get_all_users_stmt = select(UserDataModel).where( UserDataModel.is_deleted == False)
            result = await self.db.execute(get_all_users_stmt)
            users_datamodel = result.scalars().all()
            return [self._to_domain(user) for user in users_datamodel]
        except SQLAlchemyError as e:
            raise UserNotFoundError("") from e
