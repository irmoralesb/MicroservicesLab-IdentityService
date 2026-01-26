from typing import Annotated, AsyncIterator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import app_settings
from infrastructure.databases.database import get_monitored_db_session
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.role_repository import RoleRepository
from application.services.user_service import UserService
from application.services.auth_service import AuthenticateService
from application.services.token_service import TokenService
from domain.entities.user_model import UserWithRolesModel

async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a monitored async DB session per request."""
    async with get_monitored_db_session() as db:
        yield db

def get_user_repository(db: Annotated[AsyncSession, Depends(get_db_session)]) -> UserRepository:
    """Provide a `UserRepository` bound to the current DB session."""
    return UserRepository(db)

def get_role_repository(db: Annotated[AsyncSession, Depends(get_db_session)]) -> RoleRepository:
    """Provide a `RoleRepository` bound to the current DB session."""
    return RoleRepository(db)

def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
) -> UserService:
    """Provide a `UserService`."""
    return UserService(user_repo, role_repo)


# Service dependencies
async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthenticateService:
    return AuthenticateService(user_repo)


def get_token_service(
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> TokenService:
    """Provide a `TokenService` configured with settings."""
    return TokenService(
        app_settings.secret_token_key,
        app_settings.auth_algorithm,
        role_repo,
        user_repo,
    )

oauth_bearer = OAuth2PasswordBearer(tokenUrl=app_settings.token_url)

async def get_authenticated_user(
    token: Annotated[str, Depends(oauth_bearer)],
    token_svc: Annotated[TokenService, Depends(get_token_service)],
) -> UserWithRolesModel:
    """Decode the token and return the authenticated user with roles."""
    try:
        return await token_svc.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

# Clean aliases for router signatures
UserSvcDep = Annotated[UserService, Depends(get_user_service)]
AuthSvcDep = Annotated[AuthenticateService, Depends(get_auth_service)]
TokenSvcDep = Annotated[TokenService, Depends(get_token_service)]
CurrentUserDep = Annotated[UserWithRolesModel, Depends(get_authenticated_user)]