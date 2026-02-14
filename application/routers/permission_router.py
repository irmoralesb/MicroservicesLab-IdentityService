from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.routers.dependency_utils import (
    PermissionSvcDep,
    get_authenticated_user,
    require_permission,
    require_role,
)
from application.schemas.permission_schema import (
    PermissionCreateRequest,
    PermissionForRoleResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)
from domain.exceptions.permission_errors import (
    PermissionCreationError,
    PermissionDeleteError,
    PermissionNotFoundError,
    PermissionStillAssignedError,
    PermissionUpdateError,
    PermissionAssignError,
    PermissionUnassignError,
)
from domain.exceptions.services_errors import ServiceNotFoundError


router = APIRouter(
    prefix="/api/v1/permissions",
    tags=["permissions"],
    dependencies=[Depends(get_authenticated_user)],
)


@router.get(
    "",
    response_model=list[PermissionResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "read")),
    ],
)
async def list_permissions(
    service_id: UUID,
    permission_svc: PermissionSvcDep,
) -> list[PermissionResponse]:
    """List all permissions for a specific service."""
    try:
        permissions = await permission_svc.list_permissions_by_service(service_id)
        return [PermissionResponse.from_model(permission) for permission in permissions]
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching permissions: {str(exc)}",
        )


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "create")),
    ],
)
async def create_permission(
    request: PermissionCreateRequest,
    permission_svc: PermissionSvcDep,
) -> PermissionResponse:
    """Create a new permission."""
    try:
        created_permission = await permission_svc.create_permission(request.to_model())
        return PermissionResponse.from_model(created_permission)
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except (PermissionCreationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating permission: {str(exc)}",
        )


@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "update")),
    ],
)
async def update_permission(
    permission_id: UUID,
    request: PermissionUpdateRequest,
    permission_svc: PermissionSvcDep,
) -> PermissionResponse:
    """Update an existing permission."""
    try:
        # Get existing permission to retrieve service_id
        existing_permission = await permission_svc.get_permission(permission_id)
        updated_permission = await permission_svc.update_permission(
            request.to_model(permission_id, existing_permission.service_id)
        )
        return PermissionResponse.from_model(updated_permission)
    except PermissionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except (PermissionUpdateError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating permission: {str(exc)}",
        )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "delete")),
    ],
)
async def delete_permission(
    permission_id: UUID,
    permission_svc: PermissionSvcDep,
) -> dict:
    """Delete a permission. Fails if the permission is still assigned to any role."""
    try:
        success = await permission_svc.delete_permission(permission_id)
        return {"success": success}
    except PermissionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except PermissionStillAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except PermissionDeleteError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting permission: {str(exc)}",
        )


# Role-Permission assignment endpoints
role_permission_router = APIRouter(
    prefix="/api/v1/roles",
    tags=["permissions"],
    dependencies=[Depends(get_authenticated_user)],
)


@role_permission_router.get(
    "/{role_id}/permissions",
    response_model=list[PermissionForRoleResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "read")),
    ],
)
async def get_permissions_for_role(
    role_id: UUID,
    service_id: UUID,
    permission_svc: PermissionSvcDep,
) -> list[PermissionForRoleResponse]:
    """Get all permissions for a service with assignment status for a specific role."""
    try:
        permissions_with_status = await permission_svc.get_permissions_for_role(
            role_id, service_id
        )
        return [
            PermissionForRoleResponse.from_model_with_status(permission, is_assigned)
            for permission, is_assigned in permissions_with_status
        ]
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching permissions for role: {str(exc)}",
        )


@role_permission_router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "update")),
    ],
)
async def assign_permission_to_role(
    role_id: UUID,
    permission_id: UUID,
    permission_svc: PermissionSvcDep,
) -> dict:
    """Assign a permission to a role."""
    try:
        success = await permission_svc.assign_permission_to_role(role_id, permission_id)
        return {"success": success}
    except PermissionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except (PermissionAssignError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning permission to role: {str(exc)}",
        )


@role_permission_router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("permission", "update")),
    ],
)
async def unassign_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    permission_svc: PermissionSvcDep,
) -> dict:
    """Unassign a permission from a role."""
    try:
        success = await permission_svc.unassign_permission_from_role(role_id, permission_id)
        return {"success": success}
    except PermissionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except (PermissionUnassignError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unassigning permission from role: {str(exc)}",
        )
