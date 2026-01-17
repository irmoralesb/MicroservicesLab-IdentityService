from pydantic import BaseModel
import uuid
class CreateUserRequest(BaseModel):
    first_name: str
    middle_name: str
    last_name: str
    email: str


class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    middle_name: str
    last_name: str
    email: str

