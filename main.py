from dotenv import load_dotenv
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from routers import auth

load_dotenv()

# Configure logging from environment (default INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
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
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
origins = [origin.strip()
           for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_ENDPOINT = os.getenv("METRICS_ENDPOINT", "/metrics")

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


app.include_router(auth.router)

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message":"Contact your Administrator to get access to the system"}


