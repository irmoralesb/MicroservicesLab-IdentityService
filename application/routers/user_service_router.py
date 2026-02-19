from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.routers.dependency_utils import (
    UserServiceMgmtSvcDep,
    get_authenticated_user,
    require_permission,
    require_role,
)
from infrastructure.observability.logging.loki_handler import get_structured_logger
from application.schemas.user_service_schema import (
    UserServiceAssignRequest,
    UserServiceResponse,
)
from application.schemas.service_schema import ServiceResponse
from domain.exceptions.services_errors import (
    AssignServiceToUserError,
    UnassignServiceFromUserError,
    ServiceNotFoundError,
    ServiceDataAccessError,
)


logger = get_structured_logger(__name__)

router = APIRouter(
    prefix="/api/v1/users/services",
    tags=["user-services"],
    dependencies=[Depends(get_authenticated_user)],
)


@router.post(
    "/assign",
    response_model=UserServiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("user", "update")),
    ],
)
async def assign_service_to_user(
    request: UserServiceAssignRequest,
    user_svc_mgmt: UserServiceMgmtSvcDep,
) -> UserServiceResponse:
    """Assign a service to a user."""
    try:
        user_service = await user_svc_mgmt.assign_service_to_user(
            request.user_id, request.service_id
        )
        return UserServiceResponse.from_model(user_service)
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except AssignServiceToUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error assigning service to user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while assigning the service to the user.",
        )


@router.delete(
    "/{user_id}/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("user", "update")),
    ],
)
async def unassign_service_from_user(
    user_id: UUID,
    service_id: UUID,
    user_svc_mgmt: UserServiceMgmtSvcDep,
) -> None:
    """Unassign a service from a user and remove all associated service roles."""
    try:
        success = await user_svc_mgmt.unassign_service_from_user(user_id, service_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User service assignment not found.",
            )
    except UnassignServiceFromUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error unassigning the service from user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while unassigning the service from the user.",
        )


@router.get(
    "/{user_id}",
    response_model=list[ServiceResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("user", "read")),
    ],
)
async def get_user_services(
    user_id: UUID,
    user_svc_mgmt: UserServiceMgmtSvcDep,
) -> list[ServiceResponse]:
    """Get all services assigned to a user."""
    try:
        services = await user_svc_mgmt.get_user_services(user_id)
        return [ServiceResponse.from_model(service) for service in services]
    except ServiceDataAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error getting service list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while getting the service list.",
        )
