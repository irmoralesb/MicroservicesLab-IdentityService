from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel
from domain.exceptions.roles_exceptions import AssignUserRoleError, RoleNotFound
from domain.interfaces.role_repository import RoleRepositoryInterface
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from infrastructure.databases.models import RolesDataModel, UserRolesDataModel


class RoleRepository(RoleRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_domain(self, db_role: RolesDataModel) -> RoleModel:
        return RoleModel(
            id=db_role.id,
            name=db_role.name,
            description=db_role.description
        )

    def _to_datamodel(self, role: RoleModel) -> RolesDataModel:
        return RolesDataModel(
            id=role.id,
            name=role.name,
            description=role.description
        )

    async def get_by_name(self, role_name: str) -> RoleModel:
        role_info_stmt = select(RolesDataModel).where(
            RolesDataModel.name == role_name)
        result = await self.db.execute(role_info_stmt)
        user_role_info = result.scalars().first()

        if not user_role_info:
            raise RoleNotFound(role_name)

        return self._to_domain(user_role_info)

    async def assign_role(self, user: UserModel, role: RoleModel) -> bool:
        if user is None:
            raise ValueError(
                "Cannot assign role to the user, no user data was provided.")

        if role is None:
            raise ValueError(
                "Cannot assign role to the user, no role data was provided.")

        try:
            create_user_role: UserRolesDataModel = UserRolesDataModel(
                user_id=user.id,
                role_id=role.id
            )

            self.db.add(create_user_role)
            await self.db.commit()
            await self.db.refresh(create_user_role)
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            return False
            #raise AssignUserRoleError(user.first_name, role.name) from e