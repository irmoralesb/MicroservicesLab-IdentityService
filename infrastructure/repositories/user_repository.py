from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.entities.user_model import UserModel
from infrastructure.databases.models import UserDataModel
from domain.exceptions.auth_exceptions import (
    UserAlreadyExistsException,
    UserCreationError,
    UserNotFoundException,
    UserUpdateError)
from domain.interfaces.user_repository import UserRepositoryInterface
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID


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
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
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

    async def create_user(self, user: UserModel) -> UserModel:
        """Add a new user"""
        if user is None:
            raise ValueError("Cannot create user, no data was provided.")

        user_exists = await self.exists_by_email(user.email)

        if user_exists:
            raise UserAlreadyExistsException(user.email)

        try:
            create_user_model = self._to_datamodel(user)
            self.db.add(create_user_model)
            await self.db.commit()
            await self.db.refresh(create_user_model)

            return self._to_domain(create_user_model)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserCreationError(user.email) from e

    async def update_user(self, user: UserModel) -> UserModel:
        """Update existing user"""

        if user is None or user.id is None:
            raise UserNotFoundException(user.email)

        try:
            get_user_to_update_stmt = select(UserDataModel).where(
                UserDataModel.id == user.id
            )
            result = await self.db.execute(get_user_to_update_stmt)
            user_to_update = result.scalars().first()

            if user_to_update is None:
                raise UserNotFoundException(user.email)
            self._update_datamodel(user, user_to_update)
            await self.db.commit()
            await self.db.refresh(user_to_update)
            return self._to_domain(user_to_update)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise UserUpdateError(user.email) from e
        

    async def get_by_email(self, email: str) -> UserModel | None:
        """Get user by email"""
        try:
            check_user_email_stmt = select(UserDataModel).where(
                UserDataModel.email == email)
            result = await self.db.execute(check_user_email_stmt)
            existing_user = result.scalars().first()

            return None if existing_user is None else self._to_domain(existing_user)
        except SQLAlchemyError as e:
            raise UserNotFoundException(email) from e

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
            raise UserNotFoundException(str(id)) from e

    async def exists_by_email(self, email: str) -> bool:
        """Check the user exist by email"""
        try:
            check_user_email_stmt = select(UserDataModel).where(
                UserDataModel.email == email)
            result = await self.db.execute(check_user_email_stmt)
            existing_user = result.scalars().first()

            return False if existing_user is None else True
        except SQLAlchemyError as e:
            raise UserNotFoundException(email) from e
