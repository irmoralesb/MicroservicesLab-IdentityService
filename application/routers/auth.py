from datetime import timedelta
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_bcrypt_context
from core.settings import app_settings
from infrastructure.databases.database import get_monitored_db_session
from infrastructure.databases.models import RolesDataModel, UserDataModel, UserRolesDataModel
from application.services.auth_service import authenticate_user, create_access_token
from ..schemas import auth_schemas as schema

router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency to provide db context."""
    async with get_monitored_db_session() as db:
        yield db



@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
        create_user_request: schema.CreateUserRequest,
        db: AsyncSession = Depends(get_db)) -> schema.UserResponse:
    # Check if user with this email already exists
    check_user_email_stmt = select(UserDataModel).where(
        UserDataModel.email == create_user_request.email)
    result = await db.execute(check_user_email_stmt)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{create_user_request.email}' already exists"
        )

    # Get the user role
    default_user_role = app_settings.default_user_role
    role_info_stmt = select(RolesDataModel).where(
        RolesDataModel.name == default_user_role)
    result = await db.execute(role_info_stmt)
    user_role_info = result.scalars().first()
    if not user_role_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Role {default_user_role} not defined."
        )

    create_user_model = UserDataModel(
        first_name=create_user_request.first_name,
        middle_name=create_user_request.middle_name,
        last_name=create_user_request.last_name,
        email=create_user_request.email,
        hashed_password=get_bcrypt_context().hash(create_user_request.password)
    )

    try:
        db.add(create_user_model)
        await db.commit()
        await db.refresh(create_user_model)

        user_role_model = UserRolesDataModel(
            user_id=create_user_model.id,
            role_id=user_role_info.id
        )

        db.add(user_role_model)
        await db.commit()
        await db.refresh(user_role_model)

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

    user_response = schema.UserResponse(
        id=create_user_model.id,
        first_name=create_user_model.first_name,
        middle_name=create_user_model.middle_name,
        last_name=create_user_model.last_name,
        email=create_user_model.email
    )

    return user_response


@router.post("/token", response_model=schema.TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user_authenticated = await authenticate_user(form_data.username, form_data.password, db)
    if not user_authenticated:
        return "Failed Authentication"

    token_time_delta = timedelta(int(app_settings.token_time_delta_in_minutes))

    token = create_access_token(
        email=user_authenticated.email,
        user_id=user_authenticated.id,
        expires_delta=token_time_delta)

    return {'access_token': token, 'token_type': 'bearer'}
