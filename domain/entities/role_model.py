from dataclasses import dataclass
from uuid import UUID

@dataclass
class RoleModel:
    id: UUID
    name: str
    description: str