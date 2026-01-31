from dotenv import load_dotenv
from core.settings import app_settings
import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.responses import JSONResponse
from domain.exceptions.auth_errors import (
    MissingPermissionError,
    MissingRoleError,
    UnauthorizedUserError
)
from application.routers import auth_router, user_profile_router
from infrastructure.observability.logging.loki_handler import (
    setup_loki_handler,
    get_structured_logger,
)
from infrastructure.observability.tracing.tempo import setup_tempo_tracer
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

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
async def permission_exception_handler(request, exc: MissingRoleError):
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


# Prometheus metrics configuration
METRICS_ENABLED = app_settings.metrics_enabled
METRICS_ENDPOINT = app_settings.metrics_endpoint

# Initialize Prometheus instrumentation with configuration
# This automatically tracks HTTP requests, response times, and status codes
if METRICS_ENABLED:
    try:
        instrumentator = Instrumentator(
            should_group_status_codes=True,  # Group 2xx, 3xx, 4xx, 5xx
            should_ignore_untemplated=True,  # Ignore requests without a route
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            # Don't track admin/metrics endpoints
            excluded_handlers=[".*admin.*", "/metrics"],
            env_var_name="METRICS_ENABLED",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )

        instrumentator.instrument(app).expose(app, endpoint=METRICS_ENDPOINT)
        logger.info(f"Prometheus metrics enabled at {METRICS_ENDPOINT}")
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus metrics: {e}")
else:
    logger.info("Prometheus metrics disabled")


# Loki logging configuration
LOKI_ENABLED = app_settings.loki_enabled

if LOKI_ENABLED:
    try:
        # Parse labels from comma-separated string
        loki_labels = {}
        for label_pair in app_settings.loki_labels.split(","):
            if "=" in label_pair:
                key, value = label_pair.split("=", 1)
                loki_labels[key.strip()] = value.strip()
        
        # Setup Loki handler
        loki_handler = setup_loki_handler(
            loki_url=app_settings.loki_url,
            labels=loki_labels,
            log_level=app_settings.min_log_level_for_loki,
            batch_interval=app_settings.loki_batch_interval,
            timeout=app_settings.loki_timeout,
        )
        
        # Add Loki handler to root logger to capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(loki_handler)
        
        logger.info(
            f"Loki logging enabled at {app_settings.loki_url} "
            f"with labels: {loki_labels}"
        )
        
        # Log application startup event
        startup_logger = get_structured_logger("startup")
        startup_logger.info(
            "Identity Service started",
            extra={
                "event_type": "application_startup",
                "service_name": app_settings.service_name,
                "log_level": LOG_LEVEL,
                "metrics_enabled": METRICS_ENABLED,
                "loki_enabled": True,
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize Loki logging: {e}", exc_info=True)
else:
    logger.info("Loki logging disabled")


# Tempo tracing configuration
TRACING_ENABLED = app_settings.tracing_enabled

if TRACING_ENABLED:
    try:
        # Setup Tempo tracer
        tracer_provider = setup_tempo_tracer(
            endpoint=app_settings.tempo_endpoint,
            service_name=app_settings.service_name,
            sample_rate=app_settings.trace_sample_rate,
            enable_console_export=app_settings.enable_trace_console_export,
        )
        
        # Instrument FastAPI automatically
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy for database tracing
        # Note: This will be applied when database engine is created
        from infrastructure.databases.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        
        logger.info(
            f"Tempo tracing enabled at {app_settings.tempo_endpoint} "
            f"(sample_rate={app_settings.trace_sample_rate})"
        )
        
        # Log tracing startup event
        startup_logger = get_structured_logger("startup")
        startup_logger.info(
            "Distributed tracing initialized",
            extra={
                "event_type": "tracing_startup",
                "service_name": app_settings.service_name,
                "tempo_endpoint": app_settings.tempo_endpoint,
                "sample_rate": app_settings.trace_sample_rate,
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize Tempo tracing: {e}", exc_info=True)
else:
    logger.info("Tempo tracing disabled")


app.include_router(auth_router.router)
app.include_router(user_profile_router.router)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Contact your Administrator to get access to the system"}
