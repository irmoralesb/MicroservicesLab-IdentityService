from __future__ import annotations

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from core.datetime_utils import parse_mssql_datetime as _parse_mssql_datetime
from domain.entities.user_service_model import UserServiceModel


class UserServiceAssignRequest(BaseModel):
    """Request to assign a service to a user."""
    user_id: UUID
    service_id: UUID


class UserServiceResponse(BaseModel):
    """Response model for user service assignment."""
    id: UUID | None
    user_id: UUID
    service_id: UUID
    assigned_at: datetime | None = None

    @field_validator("assigned_at", mode="before")
    @classmethod
    def parse_assigned_at(cls, v: object) -> datetime | None:
        return _parse_mssql_datetime(v)

    @classmethod
    def from_model(cls, user_service: UserServiceModel) -> "UserServiceResponse":
        return cls(
            id=user_service.id,
            user_id=user_service.user_id,
            service_id=user_service.service_id,
            assigned_at=user_service.assigned_at,
        )


class UserServicesResponse(BaseModel):
    """Response model for list of user services."""
    user_id: UUID
    services: list[dict] = Field(default_factory=list)

