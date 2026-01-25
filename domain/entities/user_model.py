from dataclasses import dataclass
from .role_model import RoleModel
from uuid import UUID
from typing import List
import datetime


@dataclass
class UserModel:
    id: UUID | None
    first_name: str
    last_name: str
    email: str
    middle_name: str | None = None
    hashed_password: str | None = None
    is_active: bool = False
    is_verified: bool = False
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


@dataclass
class UserModelWithRoles():
    user:UserModel
    roles: List[RoleModel] 