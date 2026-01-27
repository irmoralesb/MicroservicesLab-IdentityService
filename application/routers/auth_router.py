from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from core.settings import app_settings
from application.schemas import auth_schemas as schema
from application.routers.dependency_utils import (
    UserSvcDep, AuthSvcDep, TokenSvcDep, CurrentUserDep, require_role ,require_permission)
from domain.entities.user_model import UserModel
from domain.exceptions.auth_exceptions import MissingPermissionException


router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)


@router.post(
    "", 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin")),Depends(require_permission("user", "create"))]
)
async def create_user(
    create_user_request: schema.CreateUserRequest,
    user_svc: UserSvcDep
) -> schema.UserResponse:
    """Create a new user with default role (Admin only)"""
    
    new_user: UserModel = create_user_request._to_model()
    
    try:
        created_user = await user_svc.create_user_with_default_role(
            new_user, 
            app_settings.default_user_role
        )
        
        return schema.UserResponse.from_UserModel(created_user)
        
    except MissingPermissionException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while creating the user: {str(e)}"
        )


@router.post("/token", response_model=schema.TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_svc: AuthSvcDep,
    token_svc: TokenSvcDep
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

    token_time_delta = timedelta(minutes=int(
        app_settings.token_time_delta_in_minutes))

    token = await token_svc.create_access_token(
        user=user_authenticated,
        expires_delta=token_time_delta
    )

    return {'access_token': token, 'token_type': 'bearer'}
