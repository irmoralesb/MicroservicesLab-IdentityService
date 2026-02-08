from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.routers.dependency_utils import (
    ServiceSvcDep,
    get_authenticated_user,
    require_permission,
    require_role,
)
from application.schemas.service_schema import ServiceCreateRequest, ServiceResponse
from domain.exceptions.services_errors import ServiceCreationError, ServiceNotFoundError


router = APIRouter(
    prefix="/api/v1/services",
    tags=["services"],
    dependencies=[Depends(get_authenticated_user)],
)


@router.get(
    "",
    response_model=list[ServiceResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("service", "read")),
    ],
)
async def get_services(service_svc: ServiceSvcDep) -> list[ServiceResponse]:
    try:
        services = await service_svc.get_all_services()
        return [ServiceResponse.from_model(service) for service in services]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching services: {str(exc)}",
        )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("service", "read")),
    ],
)
async def get_service(service_id: UUID, service_svc: ServiceSvcDep) -> ServiceResponse:
    try:
        service = await service_svc.get_service(service_id)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found.",
            )
        return ServiceResponse.from_model(service)
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching service: {str(exc)}",
        )


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_role("admin")),
        Depends(require_permission("service", "create")),
    ],
)
async def create_service(
    request: ServiceCreateRequest,
    service_svc: ServiceSvcDep,
) -> ServiceResponse:
    try:
        created_service = await service_svc.create_service(request.to_model())
        return ServiceResponse.from_model(created_service)
    except ServiceCreationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating service: {str(exc)}",
        )
