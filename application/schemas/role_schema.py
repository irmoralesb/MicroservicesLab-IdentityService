from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities.role_model import RoleModel


class RoleCreateRequest(BaseModel):
    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=200)
    service_id: UUID

    def to_model(self) -> RoleModel:
        return RoleModel(
            id=None,
            name=self.name,
            description=self.description,
            service_id=self.service_id,
        )


class RoleUpdateRequest(BaseModel):
    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=200)
    service_id: Optional[UUID] = None

    def to_model(self, role_id: UUID) -> RoleModel:
        return RoleModel(
            id=role_id,
            name=self.name,
            description=self.description,
            service_id=self.service_id,
        )


class RoleResponse(BaseModel):
    id: UUID | None
    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=200)
    service_id: UUID | None

    @classmethod
    def from_model(cls, role: RoleModel) -> "RoleResponse":
        return cls(
            id=role.id,
            name=role.name,
            description=role.description,
            service_id=role.service_id,
        )


class RoleAssignRequest(BaseModel):
    user_id: UUID
    role_id: UUID


class PermissionCheckResponse(BaseModel):
    has_permission: bool


class PermissionEntry(BaseModel):
    service_name: str
    resource: str
    action: str
    name: str
    source: str
