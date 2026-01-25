from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from core.settings import app_settings
from application.services.auth_service import AuthenticateService
from application.services.token_service import TokenService
from ..schemas import auth_schemas as schema
from infrastructure.databases.database import get_monitored_db_session
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.role_repository import RoleRepository
from domain.entities.role_model import RoleModel
from domain.entities.user_model import UserModel, UserModelWithRoles
from typing import Annotated

router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)


async def get_db():
    async with get_monitored_db_session() as db:
        yield db


async def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


async def get_role_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> RoleRepository:
    return RoleRepository(db)


async def get_auth_service() -> AuthenticateService:
    return AuthenticateService()


async def get_token_service() -> TokenService:
    return TokenService(app_settings.secret_token_key, app_settings.auth_algorithm)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
        create_user_request: schema.CreateUserRequest,
        user_repo: Annotated[UserRepository, Depends(get_user_repository)],
        role_repo: Annotated[RoleRepository, Depends(get_role_repository)]
) -> schema.UserResponse:

    default_role_name: str = app_settings.default_user_role
    user_default_role: RoleModel = await role_repo.get_by_name(default_role_name)

    new_user: UserModel = create_user_request._to_model()
    new_user = await user_repo.create_user(new_user)

    is_success: bool = await role_repo.assign_role(new_user, user_default_role)

    if is_success:
        user_response: schema.UserResponse = schema.UserResponse.from_UserModel(
            new_user)
        return user_response

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while creating the user"
        )


@router.post("/token", response_model=schema.TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_svc: Annotated[AuthenticateService, Depends(get_auth_service)],
    token_svc: Annotated[TokenService, Depends(get_token_service)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)]
):
    user_authenticated = await auth_svc.authenticate_user(form_data.username, form_data.password, user_repo)

    if not user_authenticated or not user_authenticated.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_time_delta = timedelta(int(app_settings.token_time_delta_in_minutes))

    user_roles = await role_repo.get_user_roles(user_authenticated)

    user_with_roles: UserModelWithRoles = UserModelWithRoles( user_authenticated, user_roles)

    token = token_svc.create_access_token(
        user_with_roles=user_with_roles,
        expires_delta=token_time_delta
    )

    return {'access_token': token, 'token_type': 'bearer'}
