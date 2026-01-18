from pydantic import BaseModel, Field, EmailStr
import uuid


class CreateUserRequest(BaseModel):
    first_name: str = Field(..., max_length=50)
    middle_name: str = Field(max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str = Field(..., max_length=50)
    middle_name: str = Field(max_length=50, default='')
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)


class TokenResponse(BaseModel):
    access_token:str = Field(..., max_length=2000) # TODO: review this number
    token_type:str = Field(...,max_length=10)