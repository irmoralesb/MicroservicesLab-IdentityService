from fastapi import APIRouter, Depends, HTTPException, status
from application.schemas.user_profile_schema import UserProfile
from infrastructure.databases.database import get_monitored_db_session
from application.routers.dependency_utils import UserSvcDep, CurrentUserDep, get_authenticated_user

router = APIRouter(
    prefix='/api/v1/userprofile',
    tags=["auth"],
    dependencies=[Depends(get_authenticated_user)]
)


@router.get("/profile", response_model=UserProfile)
async def get_current_user(
        current_user: CurrentUserDep,
        user_svc: UserSvcDep):
    try:
        
        if current_user is None:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Unable to get user profile data")

        user_profile = await user_svc.get_user_profile(current_user.user.id)
        if user_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found."
            )
        
        return UserProfile.from_UserModel(user_profile)
        
    except ValueError as e:
        # TODO: Log the error: e
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Error validating token data.")
