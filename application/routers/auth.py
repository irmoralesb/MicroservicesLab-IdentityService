from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from core.settings import app_settings
from application.services.auth_service import AuthenticateService
from application.services.token_service import TokenService
from application.services.user_service import UserService
from application.schemas import auth_schemas as schema
from infrastructure.databases.database import get_monitored_db_session
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.role_repository import RoleRepository
from domain.entities.user_model import UserModel

router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)


# Database session dependency
async def get_db():
    async with get_monitored_db_session() as db:
        yield db


# Repository dependencies
async def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


async def get_role_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> RoleRepository:
    return RoleRepository(db)


# Service dependencies
async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthenticateService:
    return AuthenticateService(user_repo)


async def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)]
) -> UserService:
    return UserService(user_repo, role_repo)


async def get_token_service(
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)]
) -> TokenService:
    return TokenService(
        app_settings.secret_token_key, 
        app_settings.auth_algorithm,
        role_repo
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    create_user_request: schema.CreateUserRequest,
    user_svc: Annotated[UserService, Depends(get_user_service)]
) -> schema.UserResponse:
    """Create a new user with default role"""
    
    new_user: UserModel = create_user_request._to_model()
    
    try:
        created_user = await user_svc.create_user_with_default_role(
            new_user, 
            app_settings.default_user_role
        )
        
        return schema.UserResponse.from_UserModel(created_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while creating the user: {str(e)}"
        )


@router.post("/token", response_model=schema.TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_svc: Annotated[AuthenticateService, Depends(get_auth_service)],
    token_svc: Annotated[TokenService, Depends(get_token_service)]
):
    """Authenticate user and return access token"""
    
    user_authenticated = await auth_svc.authenticate_user(
        form_data.username, 
        form_data.password
    )

    if not user_authenticated or not user_authenticated.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_time_delta = timedelta(minutes=int(app_settings.token_time_delta_in_minutes))

    token = await token_svc.create_access_token(
        user=user_authenticated,
        expires_delta=token_time_delta
    )

    return {'access_token': token, 'token_type': 'bearer'}