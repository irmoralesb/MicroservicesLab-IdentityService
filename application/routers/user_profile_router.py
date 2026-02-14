from fastapi import APIRouter, Depends, HTTPException, status
from application.schemas.user_profile_schema import UserProfileResponse, UpdateProfileRequest
from application.routers.dependency_utils import (
    AuthzSvcDep,
    CurrentUserDep,
    UserSvcDep,
    get_authenticated_user,
    require_permission,
    require_role,
)
from uuid import UUID

router = APIRouter(
    prefix='/api/v1/profile',
    tags=["profile"],
    dependencies=[Depends(get_authenticated_user)]
)


@router.get("/all",
            dependencies=[Depends(require_role("admin")), Depends(
                require_permission("user", "read"))],
            status_code=status.HTTP_200_OK)
async def get_all_users(user_svc: UserSvcDep):
    try:
        user_list = await user_svc.get_user_list()

        return [UserProfileResponse.from_user_model(user) for user in user_list]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while processing the request."
        )


@router.get("/current", response_model=UserProfileResponse)
async def get_current_user(
        current_user: CurrentUserDep,
        user_svc: UserSvcDep):
    try:

        if current_user is None or current_user.user is None or current_user.user.id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Unable to get user profile data")

        user_profile = await user_svc.get_user_profile(current_user.user.id)
        if user_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found."
            )

        return UserProfileResponse.from_user_model(user_profile)

    except ValueError as e:
        # TODO: Log the error: e
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Error validating token data.")


@router.get("/{user_id}",
            response_model=UserProfileResponse,
            dependencies=[
                Depends(require_role("admin")),
                Depends(require_permission("user", "read"))],
            status_code=status.HTTP_200_OK)
async def get_user_profile(user_id: UUID, user_svc: UserSvcDep):
    try:
        user = await user_svc.get_user_profile(user_id=user_id)

        if user:
            return UserProfileResponse.from_user_model(user)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error while processing the request"
        )


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_current_user(
    user_id: UUID,
    update_user_request: UpdateProfileRequest,
    current_user: CurrentUserDep,
    user_svc: UserSvcDep,
    authz_svc: AuthzSvcDep,
):
    try:
        if update_user_request is None or current_user is None or current_user.user is None or current_user.user.id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to update user profile data")

        is_admin = authz_svc.check_role(current_user, "admin")
        if not is_admin and current_user.user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile",
            )

        user_profile = await user_svc.get_user_profile(user_id)

        if user_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user_profile.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account deactivated"
            )

        update_user_request.update_user_model(user_profile)

        updated_user_profile = await user_svc.update_user_profile(user_profile)
        return UserProfileResponse.from_user_model(updated_user_profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error updating the user.")


@router.put("/{user_id}/activate",
            dependencies=[Depends(require_role("admin")), Depends(
                require_permission("user", "update"))],
            status_code=status.HTTP_202_ACCEPTED)
async def activate_user(
    user_id: UUID,
    user_svc: UserSvcDep
):

    try:
        user_to_activate = await user_svc.get_user_profile(user_id)

        if user_to_activate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await user_svc.activate_user(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating the user"
        )


@router.put("/{user_id}/deactivate",
            dependencies=[Depends(require_role("admin")), Depends(
                require_permission("user", "update"))],
            status_code=status.HTTP_202_ACCEPTED)
async def deactivate_user(
    user_id: UUID,
    user_svc: UserSvcDep
):

    try:
        user_to_activate = await user_svc.get_user_profile(user_id)

        if user_to_activate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await user_svc.deactivate_user(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating the user"
        )


@router.delete("/{user_id}",
               dependencies=[Depends(require_role("admin")), Depends(
                   require_permission("user", "delete"))],
               status_code=status.HTTP_202_ACCEPTED)
async def delete_user(
    user_id: UUID,
    user_svc: UserSvcDep
):

    try:
        user_to_activate = await user_svc.get_user_profile(user_id)

        if user_to_activate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await user_svc.delete_user(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating the user"
        )
