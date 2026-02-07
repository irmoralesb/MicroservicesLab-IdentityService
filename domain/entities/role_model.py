from dataclasses import dataclass
from uuid import UUID

@dataclass
class RoleModel:
    id: UUID
    service: str
    name: str
    description: str
    service_id: UUID | None = None