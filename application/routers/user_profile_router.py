from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from core.settings import app_settings
from application.services.token_service import TokenService
from application.services.user_service import UserService
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.role_repository import RoleRepository
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.databases.database import get_monitored_db_session
from domain.entities.user_model import UserModel, UserWithRolesModel


router = APIRouter(
    prefix='/api/v1/userprofile',
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


async def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)]
) -> UserService:
    return UserService(user_repo, role_repo)


async def get_token_service(
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> TokenService:
    return TokenService(
        app_settings.secret_token_key,
        app_settings.auth_algorithm,
        role_repo,
        user_repo
    )

oauth_bearer = OAuth2PasswordBearer(tokenUrl=app_settings.token_url)

async def get_authenticated_user(
    token: Annotated[str, Depends(oauth_bearer)],
    token_svc: Annotated[TokenService, Depends(get_token_service)],
) -> UserWithRolesModel:
    try:
        return await token_svc.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )



@router.get("/profile",response_model=UserModel)
async def get_current_user(
        current_user: Annotated[UserWithRolesModel, Depends(get_authenticated_user)],
        user_svc: Annotated[UserService, Depends(get_user_service)]):
    try:
        
        if current_user is None:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Unable to get user profile data")

        user_profile = user_svc.get_user_profile(current_user.user.id)
        if user_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found."
            )
    except ValueError as e:
        # TODO: Log the error: e
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Error validating token data.")
