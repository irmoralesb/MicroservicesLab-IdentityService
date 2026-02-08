from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities.service_model import ServiceModel


class ServiceCreateRequest(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    url: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)

    def to_model(self) -> ServiceModel:
        return ServiceModel(
            id=None,
            name=self.name,
            description=self.description,
            is_active=self.is_active,
            url=self.url,
            port=self.port,
        )


class ServiceResponse(BaseModel):
    id: UUID | None
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool
    url: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)

    @classmethod
    def from_model(cls, service: ServiceModel) -> "ServiceResponse":
        return cls(
            id=service.id,
            name=service.name,
            description=service.description,
            is_active=service.is_active,
            url=service.url,
            port=service.port,
        )
