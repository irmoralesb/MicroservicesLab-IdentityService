from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from . import auth_schemas as schema
from databases.models import UserDataModel
from databases.database import get_monitored_db_session

router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)

def get_db():
    with get_monitored_db_session() as db:
        yield db

@router.post("",status_code=status.HTTP_201_CREATED)
async def create_user(
    create_user_request: schema.CreateUserRequest,
    db: AsyncSession = Depends(get_db)) -> schema.UserResponse: 
    create_user_model = UserDataModel(
        first_name = create_user_request.first_name,
        middle_name = create_user_request.middle_name,
        last_name= create_user_request.last_name,
        email = create_user_request.email,
        hashed_password = ""
    )

    db.add(create_user_model)
    await db.commit()
    await db.refresh(create_user_model)

    user_response = schema.UserResponse(
        id=create_user_model.id,
        first_name=create_user_model.first_name,
        middle_name=create_user_model.middle_name,
        last_name=create_user_model.last_name,
        email=create_user_model.email
    )

    return user_response