"""
Centralized Azure Monitor metrics definitions using OpenTelemetry Metrics API.

All metrics are exported to Application Insights / Azure Monitor via the
azure-monitor-opentelemetry distro.  The public helper functions keep the
same signatures as the former Prometheus-based module so that existing
decorators and service code continue to work without changes.
"""
import logging
from opentelemetry import metrics

logger = logging.getLogger(__name__)

# Obtain the global meter (configure_azure_monitor sets the provider)
meter = metrics.get_meter("identity-service", version="1.0.0")

# ========================================================================
# Application info — recorded as a one-time log; OTel has no Info metric
# ========================================================================
# (Application info is attached as Resource attributes during setup.)

# ========================================================================
# HTTP metrics (complementary to automatic instrumentation)
# ========================================================================
http_request_total = meter.create_counter(
    name="http_request_total",
    description="Total HTTP requests by method, endpoint, and status",
    unit="1",
)

http_request_duration_seconds = meter.create_histogram(
    name="http_request_duration_seconds",
    description="HTTP request duration in seconds",
    unit="s",
)

# ========================================================================
# Authentication metrics
# ========================================================================
authentication_attempts_total = meter.create_counter(
    name="authentication_attempts_total",
    description="Total number of authentication attempts",
    unit="1",
)

authentication_duration_seconds = meter.create_histogram(
    name="authentication_duration_seconds",
    description="Time spent processing authentication requests",
    unit="s",
)

failed_login_attempts = meter.create_counter(
    name="failed_login_attempts_total",
    description="Total number of failed login attempts by reason",
    unit="1",
)

# ========================================================================
# Token metrics
# ========================================================================
token_operations_total = meter.create_counter(
    name="token_operations_total",
    description="Total number of token operations",
    unit="1",
)

token_generation_duration_seconds = meter.create_histogram(
    name="token_generation_duration_seconds",
    description="Time spent generating tokens",
    unit="s",
)

active_tokens_counter = meter.create_up_down_counter(
    name="active_tokens",
    description="Number of active tokens (delta-based)",
    unit="1",
)

token_expiration_seconds = meter.create_histogram(
    name="token_expiration_seconds",
    description="Token expiration time distribution",
    unit="s",
)

# ========================================================================
# User management metrics
# ========================================================================
user_operations_total = meter.create_counter(
    name="user_operations_total",
    description="Total number of user operations",
    unit="1",
)

user_registration_duration_seconds = meter.create_histogram(
    name="user_registration_duration_seconds",
    description="Time spent processing user registration",
    unit="s",
)

total_users_counter = meter.create_up_down_counter(
    name="total_users",
    description="Total number of users in the system (delta-based)",
    unit="1",
)

# ========================================================================
# Password operations metrics
# ========================================================================
password_operations_total = meter.create_counter(
    name="password_operations_total",
    description="Total number of password operations",
    unit="1",
)

password_strength_score = meter.create_histogram(
    name="password_strength_score",
    description="Password strength score distribution",
    unit="1",
)

# ========================================================================
# Role and permission metrics
# ========================================================================
role_operations_total = meter.create_counter(
    name="role_operations_total",
    description="Total number of role operations",
    unit="1",
)

permission_checks_total = meter.create_counter(
    name="permission_checks_total",
    description="Total number of permission checks",
    unit="1",
)

permission_check_duration_seconds = meter.create_histogram(
    name="permission_check_duration_seconds",
    description="Time spent checking permissions",
    unit="s",
)

# ========================================================================
# Session management metrics
# ========================================================================
active_sessions_counter = meter.create_up_down_counter(
    name="active_sessions",
    description="Number of active user sessions (delta-based)",
    unit="1",
)

session_operations_total = meter.create_counter(
    name="session_operations_total",
    description="Total number of session operations",
    unit="1",
)

session_duration_seconds = meter.create_histogram(
    name="session_duration_seconds",
    description="User session duration distribution",
    unit="s",
)

# ========================================================================
# Database metrics
# ========================================================================
database_connections_active_counter = meter.create_up_down_counter(
    name="database_connections_active",
    description="Number of active database connections (delta-based)",
    unit="1",
)

database_operations_total = meter.create_counter(
    name="database_operations_total",
    description="Total number of database operations",
    unit="1",
)

database_operation_duration_seconds = meter.create_histogram(
    name="database_operation_duration_seconds",
    description="Duration of database operations",
    unit="s",
)

# ========================================================================
# Error tracking
# ========================================================================
application_errors_total = meter.create_counter(
    name="application_errors_total",
    description="Total number of application errors",
    unit="1",
)

# ========================================================================
# Security metrics
# ========================================================================
security_events_total = meter.create_counter(
    name="security_events_total",
    description="Total number of security events",
    unit="1",
)


# ========================================================================
# Helper functions (same signatures as the former Prometheus module)
# ========================================================================


def record_authentication_metrics(
    auth_type: str,
    duration: float,
    status: str,
    failure_reason: str | None = None,
) -> None:
    """Record all authentication-related metrics in one call."""
    try:
        authentication_attempts_total.add(
            1, {"auth_type": auth_type, "status": status}
        )
        authentication_duration_seconds.record(
            duration, {"auth_type": auth_type, "status": status}
        )
        if status == "failure" and failure_reason:
            failed_login_attempts.add(1, {"reason": failure_reason})
    except Exception as e:
        logger.error(f"Error recording authentication metrics: {e}")


def record_token_metrics(
    operation_type: str,
    token_type: str,
    duration: float,
    status: str,
    expiration_seconds: int | None = None,
) -> None:
    """Record all token-related metrics in one call."""
    try:
        token_operations_total.add(
            1,
            {
                "operation_type": operation_type,
                "token_type": token_type,
                "status": status,
            },
        )
        if operation_type == "generate":
            token_generation_duration_seconds.record(
                duration, {"token_type": token_type}
            )
            if expiration_seconds:
                token_expiration_seconds.record(
                    expiration_seconds, {"token_type": token_type}
                )
    except Exception as e:
        logger.error(f"Error recording token metrics: {e}")


def record_user_operation_metrics(
    operation_type: str,
    duration: float,
    status: str,
) -> None:
    """Record user management operation metrics."""
    try:
        user_operations_total.add(
            1, {"operation_type": operation_type, "status": status}
        )
        if operation_type == "create":
            user_registration_duration_seconds.record(
                duration, {"status": status}
            )
    except Exception as e:
        logger.error(f"Error recording user operation metrics: {e}")


def record_password_operation_metrics(
    operation_type: str,
    status: str,
    strength_score: int | None = None,
) -> None:
    """Record password operation metrics."""
    try:
        password_operations_total.add(
            1, {"operation_type": operation_type, "status": status}
        )
        if strength_score is not None:
            password_strength_score.record(strength_score)
    except Exception as e:
        logger.error(f"Error recording password operation metrics: {e}")


def record_permission_check_metrics(
    resource: str,
    action: str,
    result: str,
    duration: float,
) -> None:
    """Record permission check metrics."""
    try:
        permission_checks_total.add(
            1, {"resource": resource, "action": action, "result": result}
        )
        permission_check_duration_seconds.record(
            duration, {"resource": resource}
        )
    except Exception as e:
        logger.error(f"Error recording permission check metrics: {e}")


def record_database_metrics(
    operation_type: str,
    table: str,
    duration: float,
    status: str = "success",
) -> None:
    """Record database operation metrics."""
    try:
        database_operations_total.add(
            1,
            {"operation_type": operation_type, "table": table, "status": status},
        )
        database_operation_duration_seconds.record(
            duration, {"operation_type": operation_type, "table": table}
        )
    except Exception as e:
        logger.error(f"Error recording database metrics: {e}")


def database_connections_activating() -> None:
    """Increment active database connections counter."""
    try:
        database_connections_active_counter.add(1)
    except Exception as e:
        logger.error(f"Error recording database connection activation: {e}")


def database_connections_deactivating() -> None:
    """Decrement active database connections counter."""
    try:
        database_connections_active_counter.add(-1)
    except Exception as e:
        logger.error(f"Error recording database connection deactivation: {e}")


def record_security_event(
    event_type: str,
    severity: str,
) -> None:
    """Record security event metrics."""
    try:
        security_events_total.add(
            1, {"event_type": event_type, "severity": severity}
        )
    except Exception as e:
        logger.error(f"Error recording security event metrics: {e}")


def active_sessions_incrementing() -> None:
    """Increment active sessions counter."""
    try:
        active_sessions_counter.add(1)
    except Exception as e:
        logger.error(f"Error incrementing active sessions: {e}")


def active_sessions_decrementing() -> None:
    """Decrement active sessions counter."""
    try:
        active_sessions_counter.add(-1)
    except Exception as e:
        logger.error(f"Error decrementing active sessions: {e}")


def update_active_tokens_gauge(token_type: str, count: int) -> None:
    """
    Update the active tokens metric.

    Note: OTel UpDownCounter is delta-based; callers should track previous
    values externally if absolute-set semantics are needed.  For simplicity
    this helper just adds the *count* as a delta.
    """
    try:
        active_tokens_counter.add(count, {"token_type": token_type})
    except Exception as e:
        logger.error(f"Error updating active tokens gauge: {e}")


def update_total_users_gauge(status: str, count: int) -> None:
    """
    Update the total users metric (delta-based).
    """
    try:
        total_users_counter.add(count, {"status": status})
    except Exception as e:
        logger.error(f"Error updating total users gauge: {e}")
