from domain.entities.permission_model import PermissionModel
from domain.exceptions.permission_errors import (
    PermissionNotFoundError,
    PermissionCreationError,
    PermissionUpdateError,
    PermissionDeleteError,
    PermissionStillAssignedError,
)
from domain.interfaces.permission_repository import PermissionRepositoryInterface
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from infrastructure.databases.models import (
    PermissionsDataModel,
    RolePermissionsDataModel,
)
from typing import List
from infrastructure.observability.metrics.decorators import track_database_operation
from uuid import UUID


class PermissionRepository(PermissionRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_domain(self, db_permission: PermissionsDataModel) -> PermissionModel:
        """Convert database model to domain model."""
        return PermissionModel(
            id=db_permission.id,
            service_id=db_permission.service_id,
            name=db_permission.name,
            resource=db_permission.resource,
            action=db_permission.action,
            description=db_permission.description,
        )

    def _to_datamodel(self, permission: PermissionModel) -> PermissionsDataModel:
        """Convert domain model to database model."""
        return PermissionsDataModel(
            id=permission.id,
            service_id=permission.service_id,
            name=permission.name,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
        )

    def _update_datamodel(self, permission: PermissionModel, permission_data: PermissionsDataModel) -> None:
        """Update permission data model values from a permission model."""
        permission_data.name = permission.name
        permission_data.resource = permission.resource
        permission_data.action = permission.action
        permission_data.description = permission.description

    @track_database_operation(operation_type='select', table='permissions')
    async def get_by_id(self, permission_id: UUID) -> PermissionModel:
        """Get a permission by its ID."""
        try:
            permission_stmt = select(PermissionsDataModel).where(
                PermissionsDataModel.id == permission_id
            )
            result = await self.db.execute(permission_stmt)
            db_permission = result.scalars().first()

            if db_permission is None:
                raise PermissionNotFoundError(permission_id)

            return self._to_domain(db_permission)
        except PermissionNotFoundError:
            raise
        except SQLAlchemyError as e:
            raise PermissionNotFoundError(permission_id) from e

    @track_database_operation(operation_type='select', table='permissions')
    async def get_all_by_service(self, service_id: UUID) -> List[PermissionModel]:
        """Get all permissions for a specific service."""
        try:
            permissions_stmt = select(PermissionsDataModel).where(
                PermissionsDataModel.service_id == service_id
            ).order_by(PermissionsDataModel.resource, PermissionsDataModel.action)

            result = await self.db.execute(permissions_stmt)
            permission_data = result.scalars().all()
            return [self._to_domain(permission) for permission in permission_data]
        except SQLAlchemyError as e:
            raise PermissionCreationError(f"Error fetching permissions for service {service_id}") from e

    @track_database_operation(operation_type='insert', table='permissions')
    async def create(self, permission: PermissionModel) -> PermissionModel:
        """Create a new permission."""
        if permission is None:
            raise ValueError("Cannot create permission, no data was provided.")

        try:
            permission_db = self._to_datamodel(permission)
            self.db.add(permission_db)
            await self.db.commit()
            await self.db.refresh(permission_db)

            return self._to_domain(permission_db)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise PermissionCreationError(permission.name) from e

    @track_database_operation(operation_type='update', table='permissions')
    async def update(self, permission: PermissionModel) -> PermissionModel:
        """Update an existing permission."""
        if permission is None or permission.id is None:
            raise PermissionNotFoundError("Unknown")

        try:
            get_permission_stmt = select(PermissionsDataModel).where(
                PermissionsDataModel.id == permission.id
            )
            result = await self.db.execute(get_permission_stmt)
            permission_data = result.scalars().first()

            if permission_data is None:
                raise PermissionNotFoundError(permission.id)

            self._update_datamodel(permission, permission_data)
            await self.db.commit()
            await self.db.refresh(permission_data)

            return self._to_domain(permission_data)
        except PermissionNotFoundError:
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise PermissionUpdateError(permission.id) from e

    @track_database_operation(operation_type='delete', table='permissions')
    async def delete(self, permission_id: UUID) -> bool:
        """Delete a permission by ID."""
        if permission_id is None:
            raise PermissionNotFoundError("Unknown")

        try:
            # First check if permission is assigned to any role
            if await self.is_assigned_to_any_role(permission_id):
                raise PermissionStillAssignedError(permission_id)

            get_permission_stmt = select(PermissionsDataModel).where(
                PermissionsDataModel.id == permission_id
            )
            result = await self.db.execute(get_permission_stmt)
            permission_data = result.scalars().first()

            if permission_data is None:
                raise PermissionNotFoundError(permission_id)

            await self.db.delete(permission_data)
            await self.db.commit()
            return True
        except (PermissionNotFoundError, PermissionStillAssignedError):
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise PermissionDeleteError(permission_id) from e

    @track_database_operation(operation_type='select', table='permissions')
    async def get_permissions_for_role(self, role_id: UUID, service_id: UUID) -> List[tuple[PermissionModel, bool]]:
        """
        Get all permissions for a service with assignment status for a specific role.
        Returns list of tuples: (permission, is_assigned)
        """
        try:
            # Get all permissions for the service
            all_permissions_stmt = select(PermissionsDataModel).where(
                PermissionsDataModel.service_id == service_id
            ).order_by(PermissionsDataModel.resource, PermissionsDataModel.action)

            all_permissions_result = await self.db.execute(all_permissions_stmt)
            all_permissions = all_permissions_result.scalars().all()

            # Get assigned permission IDs for this role
            assigned_permissions_stmt = select(
                RolePermissionsDataModel.permission_id
            ).where(
                RolePermissionsDataModel.role_id == role_id
            )
            assigned_result = await self.db.execute(assigned_permissions_stmt)
            assigned_permission_ids = {row[0] for row in assigned_result.all()}

            # Build result list with assignment status
            result = []
            for permission in all_permissions:
                is_assigned = permission.id in assigned_permission_ids
                result.append((self._to_domain(permission), is_assigned))

            return result
        except SQLAlchemyError as e:
            raise PermissionCreationError(
                f"Error fetching permissions for role {role_id}"
            ) from e

    @track_database_operation(operation_type='insert', table='role_permissions')
    async def assign_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Assign a permission to a role."""
        if role_id is None:
            raise ValueError("Cannot assign permission, no role id was provided.")

        if permission_id is None:
            raise ValueError("Cannot assign permission, no permission id was provided.")

        try:
            # Check if already assigned (avoid duplicate error)
            check_stmt = select(RolePermissionsDataModel).where(
                RolePermissionsDataModel.role_id == role_id,
                RolePermissionsDataModel.permission_id == permission_id,
            )
            check_result = await self.db.execute(check_stmt)
            existing = check_result.scalars().first()

            if existing:
                return True  # Already assigned, consider it success

            role_permission = RolePermissionsDataModel(
                role_id=role_id,
                permission_id=permission_id
            )

            self.db.add(role_permission)
            await self.db.commit()
            await self.db.refresh(role_permission)
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise PermissionCreationError(
                f"Error assigning permission '{permission_id}' to role {role_id}: {str(e)}"
            ) from e

    @track_database_operation(operation_type='delete', table='role_permissions')
    async def unassign_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Unassign a permission from a role."""
        if role_id is None:
            raise ValueError("Cannot unassign permission, no role id was provided.")

        if permission_id is None:
            raise ValueError("Cannot unassign permission, no permission id was provided.")

        try:
            role_permission_stmt = select(RolePermissionsDataModel).where(
                RolePermissionsDataModel.role_id == role_id,
                RolePermissionsDataModel.permission_id == permission_id,
            )
            result = await self.db.execute(role_permission_stmt)
            role_permission = result.scalars().first()

            if role_permission is None:
                return False  # Not assigned, consider it success

            await self.db.delete(role_permission)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise PermissionDeleteError(permission_id) from e

    @track_database_operation(operation_type='select', table='role_permissions')
    async def is_assigned_to_any_role(self, permission_id: UUID) -> bool:
        """Check if a permission is assigned to any role."""
        try:
            # Check if any role_permission record exists for this permission
            check_stmt = select(RolePermissionsDataModel).where(
                RolePermissionsDataModel.permission_id == permission_id
            ).limit(1)
            result = await self.db.execute(check_stmt)
            return result.scalars().first() is not None
        except SQLAlchemyError as e:
            raise PermissionCreationError(
                f"Error checking if permission {permission_id} is assigned: {str(e)}"
            ) from e
