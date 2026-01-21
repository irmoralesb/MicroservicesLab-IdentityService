#from infrastructure.databases.database import get_monitored_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.entities.user_model import UserModel
from infrastructure.databases.models import UserDataModel
from domain.exceptions.auth_exceptions import UserAlreadyExistsException, CreateUserError
from domain.interfaces.user_repository import UserRepositoryInterface
from sqlalchemy.exc import SQLAlchemyError


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
            is_verified=db_user.is_verified
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
            is_verified=user.is_verified
        )

    async def create_user(self, user: UserModel) -> UserModel:
        """Add a new user"""
        if user is None:
            raise ValueError("Cannot create user, no data was provided.")

        user_exists = await self.exists_by_email(UserModel.email)

        if user_exists is not None:
            raise UserAlreadyExistsException(UserModel.email)

        try:
            create_user_model = self._to_datamodel(user)
            self.db.add(create_user_model)
            await self.db.commit()
            await self.db.refresh(create_user_model)

            return self._to_domain(create_user_model)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise CreateUserError(user.email) from e

        # # Get the user role
        # role_info_stmt = select(RolesDataModel).where(
        #     RolesDataModel.name == default_user_role)
        # result = await db.execute(role_info_stmt)
        # user_role_info = result.scalars().first()
        # if not user_role_info:
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Role {default_user_role} not defined."
        #     )

        # try:
        #     db.add(create_user_model)
        #     await db.commit()
        #     await db.refresh(create_user_model)

        #     user_role_model = UserRolesDataModel(
        #         user_id=create_user_model.id,
        #         role_id=user_role_info.id
        #     )

        #     db.add(user_role_model)
        #     await db.commit()
        #     await db.refresh(user_role_model)

        # except IntegrityError as e:
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="A user with this email already exists"
        #     )

    async def get_by_email(self, email: str) -> UserModel | None:
        """Get user by email"""
        check_user_email_stmt = select(UserDataModel).where(
            UserDataModel.email == email)
        result = await self.db.execute(check_user_email_stmt)
        existing_user = result.scalars().first()

        return None if existing_user is None else self._to_domain(existing_user)

    async def exists_by_email(self, email: str) -> bool:
        """Get user by email"""
        check_user_email_stmt = select(UserDataModel).where(
            UserDataModel.email == email)
        result = await self.db.execute(check_user_email_stmt)
        existing_user = result.scalars().first()

        return False if existing_user is None else True
