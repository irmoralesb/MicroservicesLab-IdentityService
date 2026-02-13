from dataclasses import dataclass
from uuid import UUID


@dataclass
class ServiceModel:
    id: UUID | None
    name: str
    description: str | None
    is_active: bool
    url: str | None
    port: int | None
