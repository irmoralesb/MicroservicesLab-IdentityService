import uuid
from datetime import datetime
from pydantic import BaseModel
from domain.entities.role_model import RoleModel

class RoleResponse(BaseModel):
    id: uuid.UUID | None
    service: str
    name: str
    description: str

