from pydantic import BaseModel, Field, EmailStr
from domain.entities.user_model import UserModel
import uuid
from datetime import datetime


class UserProfile(BaseModel):
    id: uuid.UUID | None
    first_name: str = Field(..., max_length=50)
    middle_name: str | None = Field(default=None, max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)
    is_active: bool
    is_verified: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_UserModel(cls, user: UserModel) -> "UserProfile":
        return cls(
            id=user.id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
