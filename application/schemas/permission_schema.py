from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities.permission_model import PermissionModel


class PermissionCreateRequest(BaseModel):
    service_id: UUID
    name: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=30)
    description: str = Field(..., max_length=200)

    def to_model(self) -> PermissionModel:
        return PermissionModel(
            id=None,
            service_id=self.service_id,
            name=self.name,
            resource=self.resource,
            action=self.action,
            description=self.description,
        )


class PermissionUpdateRequest(BaseModel):
    name: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=30)
    description: str = Field(..., max_length=200)

    def to_model(self, permission_id: UUID, service_id: UUID) -> PermissionModel:
        return PermissionModel(
            id=permission_id,
            service_id=service_id,
            name=self.name,
            resource=self.resource,
            action=self.action,
            description=self.description,
        )


class PermissionResponse(BaseModel):
    id: UUID
    service_id: UUID
    name: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=30)
    description: str = Field(..., max_length=200)

    @classmethod
    def from_model(cls, permission: PermissionModel) -> "PermissionResponse":
        return cls(
            id=permission.id,
            service_id=permission.service_id,
            name=permission.name,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
        )


class PermissionForRoleResponse(PermissionResponse):
    """Permission with assignment status for a specific role."""
    is_assigned: bool

    @classmethod
    def from_model_with_status(
        cls, permission: PermissionModel, is_assigned: bool
    ) -> "PermissionForRoleResponse":
        return cls(
            id=permission.id,
            service_id=permission.service_id,
            name=permission.name,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
            is_assigned=is_assigned,
        )
