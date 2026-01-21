from dataclasses import dataclass
from uuid import UUID
import datetime

@dataclass
class UserModel:
    id: UUID
    first_name: str
    last_name: str
    email: str
    middle_name: str | None = None
    hashed_password: str | None = None
    is_active: bool = False
    is_verified: bool = False
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None