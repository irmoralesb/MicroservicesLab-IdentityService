from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.routers.dependency_utils import (
    RoleSvcDep,
    UserSvcDep,
    get_authenticated_user,
    require_permission,
    require_role,
)
from application.schemas.role_schema import (
    PermissionCheckResponse,
    PermissionEntry,
    RoleAssignRequest,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from domain.exceptions.roles_errors import (
    AssignUserRoleError,
    UnassignUserRoleError,
    RoleCreationError,
    RoleDeleteError,
    RoleListError,
    RoleNotFoundError,
    RoleUpdateError,
)
from domain.exceptions.services_errors import ServiceNotFoundError


router = APIRouter(
    prefix="/api/v1/roles",
    tags=["roles"],
    dependencies=[Depends(get_authenticated_user)],
)


@router.get(
    "/{service_id}/role/{role_name}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "read")),
    ],
)
async def get_role_by_name(
    service_id: UUID,
    role_name: str,
    role_svc: RoleSvcDep,
) -> RoleResponse:
    try:
        role = await role_svc.get_role_by_name(service_id, role_name)
        return RoleResponse.from_model(role)
    except (RoleNotFoundError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching role: {str(exc)}",
        )


@router.get(
    "/{service_id}",
    response_model=list[RoleResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "read")),
    ],
)
async def get_role_list(service_id: UUID, role_svc: RoleSvcDep) -> list[RoleResponse]:
    try:
        roles = await role_svc.get_role_list(service_id)
        return [RoleResponse.from_model(role) for role in roles]
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except RoleListError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching role list: {str(exc)}",
        )


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "create")),
    ],
)
async def create_role(request: RoleCreateRequest, role_svc: RoleSvcDep) -> RoleResponse:
    try:
        created_role = await role_svc.create_role(request.to_model())
        return RoleResponse.from_model(created_role)
    except (RoleCreationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating role: {str(exc)}",
        )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "update")),
    ],
)
async def update_role(
    role_id: UUID,
    request: RoleUpdateRequest,
    role_svc: RoleSvcDep,
) -> RoleResponse:
    try:
        updated_role = await role_svc.update_role(request.to_model(role_id))
        return RoleResponse.from_model(updated_role)
    except RoleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except (RoleUpdateError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating role: {str(exc)}",
        )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "delete")),
    ],
)
async def delete_role(role_id: UUID, role_svc: RoleSvcDep) -> dict:
    try:
        success = await role_svc.delete_role(role_id)
        return {"success": success}
    except RoleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except RoleDeleteError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting role: {str(exc)}",
        )


@router.post(
    "/assign",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "assign")),
    ],
)
async def assign_role(request: RoleAssignRequest, role_svc: RoleSvcDep) -> dict:
    try:
        success = await role_svc.assign_role(request.user_id, request.role_id)
        return {"success": success}
    except (AssignUserRoleError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning role: {str(exc)}",
        )


@router.post(
    "/unassign",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "assign")),
    ],
)
async def unassign_role(request: RoleAssignRequest, role_svc: RoleSvcDep) -> dict:
    try:
        success = await role_svc.unassign_role(request.user_id, request.role_id)
        return {"success": success}
    except (UnassignUserRoleError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unassigning role: {str(exc)}",
        )


@router.get(
    "/user/{user_id}",
    response_model=list[RoleResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("role", "read")),
    ],
)
async def get_user_roles(
    user_id: UUID,
    user_svc: UserSvcDep,
    role_svc: RoleSvcDep,
) -> list[RoleResponse]:
    try:
        user = await user_svc.get_user_profile(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        roles = await role_svc.get_user_roles(user)
        return [RoleResponse.from_model(role) for role in roles]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user roles: {str(exc)}",
        )


@router.get(
    "/permissions/check",
    response_model=PermissionCheckResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "read")),
    ],
)
async def check_user_permission(
    user_id: UUID,
    service_name: str,
    resource: str,
    action: str,
    user_svc: UserSvcDep,
    role_svc: RoleSvcDep,
) -> PermissionCheckResponse:
    try:
        user = await user_svc.get_user_profile(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        has_permission = await role_svc.check_user_permission(
            user,
            service_name,
            resource,
            action,
        )
        return PermissionCheckResponse(has_permission=has_permission)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking permission: {str(exc)}",
        )


@router.get(
    "/permissions",
    response_model=list[PermissionEntry],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "read")),
    ],
)
async def get_user_permissions(
    user_id: UUID,
    user_svc: UserSvcDep,
    role_svc: RoleSvcDep,
    service_name: str | None = None,
) -> list[PermissionEntry]:
    try:
        user = await user_svc.get_user_profile(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        permissions = await role_svc.get_user_permissions(user, service_name)
        return [PermissionEntry(**permission) for permission in permissions]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching permissions: {str(exc)}",
        )
