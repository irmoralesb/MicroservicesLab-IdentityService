from dataclasses import dataclass
from uuid import UUID

@dataclass
class PermissionModel:
    id: UUID | None
    service_id: UUID
    name: str
    resource: str
    action: str
    description: str
