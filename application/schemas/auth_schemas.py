from pydantic import BaseModel, Field, EmailStr, field_validator
from domain.entities.user_model import UserModel
from core.security import get_bcrypt_context
from core.password_validator import PasswordValidator, PasswordValidationError
import uuid


class CreateUserRequest(BaseModel):
    first_name: str = Field(..., max_length=50)
    middle_name: str = Field(max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements"""
        try:
            PasswordValidator.validate(v)
        except PasswordValidationError as e:
            raise ValueError(str(e))
        return v

    def _to_model(self)-> UserModel:
        return UserModel(
            id= None,
            first_name=self.first_name,
            middle_name=self.middle_name,
            last_name=self.last_name,
            email=self.email,
            hashed_password= get_bcrypt_context().hash(self.password)
        )


class ChangePasswordRequest(BaseModel):
    """Request model for user password change"""
    current_password: str = Field(..., min_length=1, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password meets security requirements"""
        try:
            PasswordValidator.validate(v)
        except PasswordValidationError as e:
            raise ValueError(str(e))
        return v


class UnlockAccountRequest(BaseModel):
    """Request model for admin to unlock a user account"""
    user_id: uuid.UUID = Field(..., description="UUID of the user to unlock")


class UserResponse(BaseModel):
    id: uuid.UUID | None
    first_name: str = Field(..., max_length=50)
    middle_name: str|None = Field(max_length=50, default='')
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)

    @classmethod
    def from_UserModel(cls, user: UserModel) -> "UserResponse":
        return cls(
            id=user.id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email
        )


class TokenResponse(BaseModel):
    access_token:str = Field(..., max_length=2000) # TODO: review this number
    token_type:str = Field(...,max_length=10)