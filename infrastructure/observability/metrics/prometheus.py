"""
Centralized Prometheus metrics definitions.
Define all metrics here to avoid duplication across modules.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import logging


logger = logging.getLogger(__name__)

# <<   Application info metric   >>
app_info = Info('lab_identity_service', 'Application information')
app_info.info({
    'version': '1.0.0',
    'service': 'identity-api'
})

# <<   HTTP metrics (complementary to automatic instrumentation)   >>
http_request_total = Counter(
    'http_request_total',
    'Total HTTP requests by method, endpoint, and status',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# <<   Authentication metrics   >>
authentication_attempts_total = Counter(
    'authentication_attempts_total',
    'Total number of authentication attempts',
    ['auth_type', 'status']  # auth_type: login, refresh, verify; status: success, failure
)

authentication_duration_seconds = Histogram(
    'authentication_duration_seconds',
    'Time spent processing authentication requests',
    ['auth_type', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

failed_login_attempts = Counter(
    'failed_login_attempts_total',
    'Total number of failed login attempts by reason',
    ['reason']  # reason: invalid_credentials, account_locked, account_disabled, etc.
)

# <<   Token metrics   >>
token_operations_total = Counter(
    'token_operations_total',
    'Total number of token operations',
    ['operation_type', 'token_type', 'status']  # operation_type: generate, validate, revoke, refresh; token_type: access, refresh
)

token_generation_duration_seconds = Histogram(
    'token_generation_duration_seconds',
    'Time spent generating tokens',
    ['token_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

active_tokens_gauge = Gauge(
    'active_tokens',
    'Number of active tokens',
    ['token_type']
)

token_expiration_seconds = Histogram(
    'token_expiration_seconds',
    'Token expiration time distribution',
    ['token_type'],
    buckets=[300, 900, 1800, 3600, 7200, 14400, 28800, 86400, 604800]  # 5min to 7days
)

# <<   User management metrics   >>
user_operations_total = Counter(
    'user_operations_total',
    'Total number of user operations',
    ['operation_type', 'status']  # operation_type: create, update, delete, activate, deactivate
)

user_registration_duration_seconds = Histogram(
    'user_registration_duration_seconds',
    'Time spent processing user registration',
    ['status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

total_users_gauge = Gauge(
    'total_users',
    'Total number of users in the system',
    ['status']  # status: active, inactive, verified, unverified
)

# <<   Password operations metrics   >>
password_operations_total = Counter(
    'password_operations_total',
    'Total number of password operations',
    ['operation_type', 'status']  # operation_type: change, reset, validate
)

password_strength_score = Histogram(
    'password_strength_score',
    'Password strength score distribution',
    buckets=[1, 2, 3, 4, 5]
)

# <<   Role and permission metrics   >>
role_operations_total = Counter(
    'role_operations_total',
    'Total number of role operations',
    ['operation_type', 'status']  # operation_type: assign, revoke, create, delete
)

permission_checks_total = Counter(
    'permission_checks_total',
    'Total number of permission checks',
    ['resource', 'action', 'result']  # result: allowed, denied
)

permission_check_duration_seconds = Histogram(
    'permission_check_duration_seconds',
    'Time spent checking permissions',
    ['resource'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# <<   Session management metrics   >>
active_sessions_gauge = Gauge(
    'active_sessions',
    'Number of active user sessions'
)

session_operations_total = Counter(
    'session_operations_total',
    'Total number of session operations',
    ['operation_type', 'status']  # operation_type: create, terminate, validate
)

session_duration_seconds = Histogram(
    'session_duration_seconds',
    'User session duration distribution',
    buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400]  # 1min to 24hrs
)

# <<   Database metrics   >>
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_operations_total = Counter(
    'database_operations_total',
    'Total number of database operations',
    ['operation_type', 'table', 'status']  # operation_type: insert, update, select, delete
)

database_operation_duration_seconds = Histogram(
    'database_operation_duration_seconds',
    'Duration of database operations',
    ['operation_type', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# <<   Error tracking   >>
application_errors_total = Counter(
    'application_errors_total',
    'Total number of application errors',
    ['error_type', 'endpoint']
)

# <<   Security metrics   >>
security_events_total = Counter(
    'security_events_total',
    'Total number of security events',
    ['event_type', 'severity']  # event_type: brute_force, account_locked, suspicious_activity, etc.
)


def record_authentication_metrics(
    auth_type: str,
    duration: float,
    status: str,
    failure_reason: str | None = None
):
    """
    Record all authentication-related metrics in one call.
    
    Args:
        auth_type: Type of authentication ('login', 'refresh', 'verify')
        duration: Time taken for authentication in seconds
        status: Authentication status ('success' or 'failure')
        failure_reason: Reason for failure if status is 'failure'
    """
    try:
        authentication_attempts_total.labels(
            auth_type=auth_type,
            status=status
        ).inc()

        authentication_duration_seconds.labels(
            auth_type=auth_type,
            status=status
        ).observe(duration)

        if status == 'failure' and failure_reason:
            failed_login_attempts.labels(
                reason=failure_reason
            ).inc()
    except Exception as e:
        logger.error(f"Error recording authentication metrics: {e}")


def record_token_metrics(
    operation_type: str,
    token_type: str,
    duration: float,
    status: str,
    expiration_seconds: int | None = None
):
    """
    Record all token-related metrics in one call.
    
    Args:
        operation_type: Type of operation ('generate', 'validate', 'revoke', 'refresh')
        token_type: Type of token ('access', 'refresh')
        duration: Operation duration in seconds
        status: Operation status ('success' or 'failure')
        expiration_seconds: Token expiration time in seconds (for generation)
    """
    try:
        token_operations_total.labels(
            operation_type=operation_type,
            token_type=token_type,
            status=status
        ).inc()

        if operation_type == 'generate':
            token_generation_duration_seconds.labels(
                token_type=token_type
            ).observe(duration)
            
            if expiration_seconds:
                token_expiration_seconds.labels(
                    token_type=token_type
                ).observe(expiration_seconds)
    except Exception as e:
        logger.error(f"Error recording token metrics: {e}")


def record_user_operation_metrics(
    operation_type: str,
    duration: float,
    status: str
):
    """
    Record user management operation metrics.
    
    Args:
        operation_type: Type of operation ('create', 'update', 'delete', 'activate', 'deactivate')
        duration: Operation duration in seconds
        status: Operation status ('success' or 'failure')
    """
    try:
        user_operations_total.labels(
            operation_type=operation_type,
            status=status
        ).inc()

        if operation_type == 'create':
            user_registration_duration_seconds.labels(
                status=status
            ).observe(duration)
    except Exception as e:
        logger.error(f"Error recording user operation metrics: {e}")


def record_password_operation_metrics(
    operation_type: str,
    status: str,
    strength_score: int | None = None
):
    """
    Record password operation metrics.
    
    Args:
        operation_type: Type of operation ('change', 'reset', 'validate')
        status: Operation status ('success' or 'failure')
        strength_score: Password strength score (1-5, for password changes)
    """
    try:
        password_operations_total.labels(
            operation_type=operation_type,
            status=status
        ).inc()

        if strength_score is not None:
            password_strength_score.observe(strength_score)
    except Exception as e:
        logger.error(f"Error recording password operation metrics: {e}")


def record_permission_check_metrics(
    resource: str,
    action: str,
    result: str,
    duration: float
):
    """
    Record permission check metrics.
    
    Args:
        resource: Resource being accessed
        action: Action being performed
        result: Check result ('allowed' or 'denied')
        duration: Check duration in seconds
    """
    try:
        permission_checks_total.labels(
            resource=resource,
            action=action,
            result=result
        ).inc()

        permission_check_duration_seconds.labels(
            resource=resource
        ).observe(duration)
    except Exception as e:
        logger.error(f"Error recording permission check metrics: {e}")


def record_database_metrics(
    operation_type: str,
    table: str,
    duration: float,
    status: str = 'success'
):
    """
    Record database operation metrics.
    
    Args:
        operation_type: Type of operation ('insert', 'update', 'select', 'delete')
        table: Table name
        duration: Operation duration in seconds
        status: Operation status ('success' or 'error')
    """
    try:
        database_operations_total.labels(
            operation_type=operation_type,
            table=table,
            status=status
        ).inc()

        database_operation_duration_seconds.labels(
            operation_type=operation_type,
            table=table
        ).observe(duration)
    except Exception as e:
        logger.error(f"Error recording database metrics: {e}")


def database_connections_activating():
    """Increment active database connections counter."""
    try:
        database_connections_active.inc()
    except Exception as e:
        logger.error(f"Error recording database connection activation: {e}")


def database_connections_deactivating():
    """Decrement active database connections counter."""
    try:
        database_connections_active.dec()
    except Exception as e:
        logger.error(f"Error recording database connection deactivation: {e}")


def record_security_event(
    event_type: str,
    severity: str
):
    """
    Record security event metrics.
    
    Args:
        event_type: Type of security event ('brute_force', 'account_locked', 'suspicious_activity', etc.)
        severity: Event severity ('low', 'medium', 'high', 'critical')
    """
    try:
        security_events_total.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    except Exception as e:
        logger.error(f"Error recording security event metrics: {e}")


def active_sessions_incrementing():
    """Increment active sessions counter."""
    try:
        active_sessions_gauge.inc()
    except Exception as e:
        logger.error(f"Error incrementing active sessions: {e}")


def active_sessions_decrementing():
    """Decrement active sessions counter."""
    try:
        active_sessions_gauge.dec()
    except Exception as e:
        logger.error(f"Error decrementing active sessions: {e}")


def update_active_tokens_gauge(token_type: str, count: int):
    """
    Update the active tokens gauge with current count.
    
    Args:
        token_type: Type of token ('access', 'refresh')
        count: Current count of active tokens
    """
    try:
        active_tokens_gauge.labels(token_type=token_type).set(count)
    except Exception as e:
        logger.error(f"Error updating active tokens gauge: {e}")


def update_total_users_gauge(status: str, count: int):
    """
    Update the total users gauge with current count.
    
    Args:
        status: User status ('active', 'inactive', 'verified', 'unverified')
        count: Current count of users with this status
    """
    try:
        total_users_gauge.labels(status=status).set(count)
    except Exception as e:
        logger.error(f"Error updating total users gauge: {e}")
