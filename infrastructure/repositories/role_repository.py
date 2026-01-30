from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel
from domain.exceptions.roles_exceptions import AssignUserRoleError, RoleNotFound
from domain.interfaces.role_repository import RoleRepositoryInterface
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from infrastructure.databases.models import (
    RolesDataModel,
    UserRolesDataModel,
    RolePermissionsDataModel,
    PermissionsDataModel,
    UserPermissionsDataModel)
from typing import List


class RoleRepository(RoleRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_domain(self, db_role: RolesDataModel) -> RoleModel:
        return RoleModel(
            id=db_role.id,
            service=db_role.service_name,
            name=db_role.name,
            description=db_role.description
        )

    def _to_datamodel(self, role: RoleModel) -> RolesDataModel:
        return RolesDataModel(
            id=role.id,
            service_name=role.service,
            name=role.name,
            description=role.description
        )

    async def get_by_name(self, role_name: str) -> RoleModel:
        try:
            role_info_stmt = select(RolesDataModel).where(
                RolesDataModel.name == role_name)
            result = await self.db.execute(role_info_stmt)
            user_role_info = result.scalars().first()

            if not user_role_info:
                raise RoleNotFound(role_name)

            return self._to_domain(user_role_info)
        except RoleNotFound:
            raise
        except SQLAlchemyError as e:
            raise RoleNotFound(role_name) from e

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
            raise AssignUserRoleError(
                f"Error assigning role '{role.name}' to user {user.id}: {str(e)}"
            ) from e

    async def get_user_roles(self, user: UserModel) -> List[RoleModel]:
        if user is None:
            raise ValueError(
                "Cannot get user roles, no user data was provided")

        try:
            get_role_stmt = select(RolesDataModel).join(
                UserRolesDataModel, UserRolesDataModel.role_id == RolesDataModel.id).where(UserRolesDataModel.user_id == user.id)
            result = await self.db.execute(get_role_stmt)
            role_data = result.scalars().all()
            return [self._to_domain(role) for role in role_data]
        except SQLAlchemyError as e:
            raise AssignUserRoleError(
                f"Error fetching roles for user {user.id}: {str(e)}")

    async def check_user_permission(
            self,
            user: UserModel,
            service_name: str,
            resource: str,
            action: str
    ) -> bool:
        """
        Check if user has permission through roles or direct assignment

        Args:
            user: User to check
            service_name: Microservice name (e.g., 'identity-service')
            resource: Resource type
            action: Action type

        Returns:
            bool: True if user has permission
        """
        if user is None or user.id is None:
            return False

        try:
            # Role base permission
            check_role_permission_stmt = select(RolesDataModel).join(
                UserRolesDataModel,
                UserRolesDataModel.role_id == RolesDataModel.id
            ).join(
                RolePermissionsDataModel,
                RolePermissionsDataModel.role_id == RolesDataModel.id
            ).join(
                PermissionsDataModel,
                PermissionsDataModel.id == RolePermissionsDataModel.permission_id
            ).where(
                UserRolesDataModel.user_id == user.id,
                PermissionsDataModel.service_name == service_name,
                PermissionsDataModel.resource == resource,
                PermissionsDataModel.action == action
            )

            result = await self.db.execute(check_role_permission_stmt)
            role_permission = result.scalars().first()

            if role_permission:
                return True

            # Check direct user permissions
            check_user_permission_stmt = select(PermissionsDataModel).join(
                UserPermissionsDataModel,
                UserPermissionsDataModel.permission_id == PermissionsDataModel.id
            ).where(
                UserPermissionsDataModel.user_id == user.id,
                PermissionsDataModel.service_name == service_name,
                PermissionsDataModel.resource == resource,
                PermissionsDataModel.action == action
            )

            result = await self.db.execute(check_user_permission_stmt)
            user_permission = result.scalars().first()

            return user_permission is not None

        except SQLAlchemyError as e:
            raise AssignUserRoleError(
                f"Error checking permissions for user {user.id}: {str(e)}"
            ) from e

    async def get_user_permissions(
        self,
        user: UserModel,
        service_name: str | None = None
    ) -> List[dict]:
        """
           Get all permissions for a user (both role-based and direct)

            Args:
                user: User to check
                service_name: Optional Service filter. If None it returns all services

           Returns:
               List of permission dictionaries with resource, action, source
        """

        if user is None or user.id is None:
            return []

        permissions = []

        try:

            role_permissions_stmt = select(
                PermissionsDataModel
            ).join(
                RolePermissionsDataModel,
                RolePermissionsDataModel.permission_id == PermissionsDataModel.id
            ).join(
                UserRolesDataModel,
                UserRolesDataModel.role_id == RolePermissionsDataModel.role_id
            ).where(
                UserRolesDataModel.user_id == user.id,
            )

            if service_name:
                role_permissions_stmt = role_permissions_stmt.where(
                    PermissionsDataModel.service_name == service_name
                )

            role_permissions_stmt = role_permissions_stmt.distinct()

            result = await self.db.execute(role_permissions_stmt)
            for perm in result.scalars().all():
                permissions.append({
                    'service_name': perm.service_name,
                    'resource': perm.resource,
                    'action': perm.action,
                    'name': perm.name,
                    'source': 'role'
                })

            # Get direct user permissions
            user_permissions_stmt = select(
                PermissionsDataModel
            ).join(
                UserPermissionsDataModel,
                UserPermissionsDataModel.permission_id == PermissionsDataModel.id
            ).where(
                UserPermissionsDataModel.user_id == user.id
            )

            if service_name:
                user_permissions_stmt = user_permissions_stmt.where(
                    PermissionsDataModel.service_name == service_name
                )

            result = await self.db.execute(user_permissions_stmt)
            for perm in result.scalars().all():
                permissions.append({
                    'service_name': perm.service_name,
                    'resource': perm.resource,
                    'action': perm.action,
                    'name': perm.name,
                    'source': 'direct'
                })

            return permissions
        except SQLAlchemyError as e:
            raise AssignUserRoleError(
                f"Error fetching permissions for user {user.id}: {str(e)}"
            )
