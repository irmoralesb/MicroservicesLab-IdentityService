from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from core.settings import app_settings
from application.schemas import auth_schemas as schema
from application.routers.dependency_utils import (
    UserSvcDep, AuthSvcDep, TokenSvcDep, require_role ,require_permission, CurrentUserDep)
from domain.entities.user_model import UserModel, UserWithRolesModel
from domain.exceptions.auth_errors import (
    MissingPermissionError,
    AccountLockedError,
    PasswordChangeError
)
from core.password_validator import PasswordValidationError


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
        created_user = await user_svc.create_user(
            new_user, 
            app_settings.default_user_role
        )
        
        return schema.UserResponse.from_UserModel(created_user)
        
    except MissingPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while creating the user: {str(e)}"
        )


@router.post("/login", response_model=schema.TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_svc: AuthSvcDep,
    token_svc: TokenSvcDep
):
    """Authenticate user and return access token"""

    try:
        user_authenticated = await auth_svc.authenticate_user(
            form_data.username,
            form_data.password
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )

    if not user_authenticated or not user_authenticated.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user_authenticated.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )

    token_time_delta = timedelta(minutes=int(
        app_settings.token_time_delta_in_minutes))

    token = await token_svc.create_access_token(
        user=user_authenticated,
        expires_delta=token_time_delta
    )

    return {'access_token': token, 'token_type': 'bearer'}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: schema.ChangePasswordRequest,
    current_user: CurrentUserDep,
    user_svc: UserSvcDep
):
    """Allow authenticated user to change their password"""
    
    try:
        await user_svc.change_password(
            user_id=current_user.user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        return {"message": "Password changed successfully"}
        
    except PasswordChangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PasswordValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )


@router.post(
    "/unlock-account",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin")), Depends(require_permission("user", "update"))]
)
async def unlock_account(
    request: schema.UnlockAccountRequest,
    auth_svc: AuthSvcDep
):
    """Allow admin to unlock a locked user account"""
    
    try:
        success = await auth_svc.unlock_account(request.user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Account unlocked successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unlocking account: {str(e)}"
        )
