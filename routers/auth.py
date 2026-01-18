from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from . import auth_schemas as schema
from databases.models import UserDataModel, RolesDataModel, UserRolesDataModel
from databases.database import get_monitored_db_session
from typing import AsyncIterator
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
import os
import uuid

router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)

USER_ROLE_NAME = 'User'

_secret_token_key: str | None = os.getenv("SECRET_TOKEN_KEY")
if not _secret_token_key:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No Secret Token Key found."
    )
secret_token_key = _secret_token_key

_auth_algorithm: str | None = os.getenv("AUTH_ALGORITHM")
if not _auth_algorithm:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No Auth Algorithm specified"
    )
auth_algorithm: str = _auth_algorithm

_token_time_delta_in_minutes = os.getenv("TOKEN_TIME_DELTA_IN_MINUTES", "0")
if _token_time_delta_in_minutes == "0":
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Token time delta not specified"
    )
token_time_delta_in_minutes = timedelta(
    minutes=int(_token_time_delta_in_minutes))


_bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency to provide db context."""
    async with get_monitored_db_session() as db:
        yield db


def get_bcrypt_context() -> CryptContext:
    """Dependency to provide bcrypt context for password hashing."""
    return _bcrypt_context


async def authenticate_user(email: str, password: str, db: AsyncSession) -> UserDataModel | None:
    """Checks if the user password matches the stored hashed password"""
    select_user_stmt = select(UserDataModel).where(
        UserDataModel.email == email)
    result = await db.execute(select_user_stmt)
    user = result.scalars().first()

    if not user:
        return None

    return user if _bcrypt_context.verify(password, user.hashed_password) else None


def create_access_token(email: str, user_id: uuid.UUID, expires_delta: timedelta) -> str:
    encode = {'sub': email, 'user_id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, secret_token_key, algorithm=auth_algorithm)


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
    role_info_stmt = select(RolesDataModel).where(
        RolesDataModel.name == USER_ROLE_NAME)
    result = await db.execute(role_info_stmt)
    user_role_info = result.scalars().first()
    if not user_role_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Role {USER_ROLE_NAME} not defined."
        )

    create_user_model = UserDataModel(
        first_name=create_user_request.first_name,
        middle_name=create_user_request.middle_name,
        last_name=create_user_request.last_name,
        email=create_user_request.email,
        hashed_password=_bcrypt_context.hash(create_user_request.password)
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

    token = create_access_token(
        email=user_authenticated.email,
        user_id=user_authenticated.id,
        expires_delta=token_time_delta_in_minutes)
    
    return {'access_token': token, 'token_type': 'bearer'}
