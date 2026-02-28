from dotenv import load_dotenv
from core.settings import app_settings
import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from domain.exceptions.auth_errors import (
    MissingPermissionError,
    MissingRoleError,
    UnauthorizedUserError
)
from domain.exceptions.permission_errors import (
    PermissionNotFoundError,
    PermissionStillAssignedError
)
from domain.exceptions.roles_errors import ServiceNotAssignedToUserError
from application.routers import auth_router, user_profile_router, role_router, service_router, permission_router, user_service_router
from infrastructure.observability.logging.azure_log_handler import (
    setup_azure_log_handler,
    get_structured_logger,
)

load_dotenv()

# Configure logging from environment (default INFO)
LOG_LEVEL = app_settings.log_level
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Identity Service",
    description="Service to authenticate and authorize users",
    version="1.0.0"
)

# CORS configuration
cors_origins = app_settings.cors_allow_origins
origins = [origin.strip()
           for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MissingPermissionError)
async def permission_exception_handler(request, exc: MissingPermissionError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": f"Permission denied: {str(exc)}",
            "resource": exc.resource,
            "action": exc.action
        }
    )


@app.exception_handler(MissingRoleError)
async def role_exception_handler(request, exc: MissingRoleError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": f"Role required: {str(exc)}",
            "role": exc.role_name
        }
    )


@app.exception_handler(UnauthorizedUserError)
async def unauthorized_exception_handler(request, exc: UnauthorizedUserError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)}
    )


@app.exception_handler(PermissionNotFoundError)
async def permission_not_found_exception_handler(request, exc: PermissionNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


@app.exception_handler(PermissionStillAssignedError)
async def permission_still_assigned_exception_handler(request, exc: PermissionStillAssignedError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )


@app.exception_handler(ServiceNotAssignedToUserError)
async def service_not_assigned_exception_handler(request, exc: ServiceNotAssignedToUserError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "user_id": str(exc.user_id),
            "service_id": str(exc.service_id)
        }
    )


# Azure Monitor / Application Insights configuration
AZURE_MONITOR_ENABLED = app_settings.azure_monitor_enabled

if AZURE_MONITOR_ENABLED and app_settings.applicationinsights_connection_string:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=app_settings.applicationinsights_connection_string,
            logger_name="",  # Capture root logger
            enable_live_metrics=True,
            sampling_ratio=app_settings.azure_monitor_sample_rate,
        )

        # Set up structured logging level for Azure export
        setup_azure_log_handler(log_level=app_settings.azure_monitor_log_level)

        logger.info(
            "Azure Monitor observability enabled "
            f"(sample_rate={app_settings.azure_monitor_sample_rate})"
        )

        # Log application startup event
        startup_logger = get_structured_logger("startup")
        startup_logger.info(
            "Identity Service started with Azure Monitor",
            extra={
                "event_type": "application_startup",
                "service_id": str(app_settings.service_id),
                "log_level": LOG_LEVEL,
                "azure_monitor_enabled": True,
            },
        )

    except Exception as e:
        logger.error(f"Failed to initialize Azure Monitor: {e}", exc_info=True)
else:
    logger.info("Azure Monitor disabled or connection string not set")


app.include_router(auth_router.router)
app.include_router(user_profile_router.router)
app.include_router(service_router.router)
app.include_router(user_service_router.router)
app.include_router(role_router.router)
app.include_router(permission_router.router)
app.include_router(permission_router.role_permission_router)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Contact your Administrator to get access to the system"}
