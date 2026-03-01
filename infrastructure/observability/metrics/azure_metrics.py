"""
Centralized Azure Monitor (Application Insights) metrics via OpenTelemetry.

Same logical metrics and record_* API as the previous Prometheus module.
MeterProvider must be initialized by calling init_azure_metrics(connection_string) at startup.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Initialized by init_azure_metrics; instruments are created there and stored here
_meter = None
_counter_authentication_attempts = None
_histogram_authentication_duration = None
_counter_failed_login_attempts = None
_counter_token_operations = None
_histogram_token_generation_duration = None
_histogram_token_expiration = None
_updown_active_tokens = None  # UpDownCounter per token_type
_counter_user_operations = None
_histogram_user_registration_duration = None
_updown_total_users = None  # ObservableGauge values stored here
_counter_password_operations = None
_histogram_password_strength = None
_counter_role_operations = None
_counter_permission_checks = None
_histogram_permission_check_duration = None
_updown_active_sessions = None
_counter_session_operations = None
_histogram_session_duration = None
_updown_database_connections = None
_counter_database_operations = None
_histogram_database_operation_duration = None
_counter_application_errors = None
_counter_security_events = None

# For observable-style gauges we store current values and report via callback
_gauge_active_tokens: dict[str, int] = {}
_gauge_total_users: dict[str, int] = {}


def init_azure_metrics(connection_string: str, export_interval_seconds: int = 60) -> None:
    """
    Initialize Azure Monitor metrics: set MeterProvider and create all instruments.
    Call once at application startup when Azure metrics are enabled.
    """
    global _meter
    global _counter_authentication_attempts, _histogram_authentication_duration, _counter_failed_login_attempts
    global _counter_token_operations, _histogram_token_generation_duration, _histogram_token_expiration
    global _updown_active_tokens
    global _counter_user_operations, _histogram_user_registration_duration, _updown_total_users
    global _counter_password_operations, _histogram_password_strength
    global _counter_role_operations, _counter_permission_checks, _histogram_permission_check_duration
    global _updown_active_sessions, _counter_session_operations, _histogram_session_duration
    global _updown_database_connections, _counter_database_operations, _histogram_database_operation_duration
    global _counter_application_errors, _counter_security_events

    try:
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter

        exporter = AzureMonitorMetricExporter.from_connection_string(connection_string)
        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=export_interval_seconds * 1000,
        )
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        _meter = provider.get_meter("identity_service", "1.0.0")

        _counter_authentication_attempts = _meter.create_counter(
            "authentication_attempts_total",
            unit="1",
            description="Total number of authentication attempts",
        )
        _histogram_authentication_duration = _meter.create_histogram(
            "authentication_duration_seconds",
            unit="s",
            description="Time spent processing authentication requests",
        )
        _counter_failed_login_attempts = _meter.create_counter(
            "failed_login_attempts_total",
            unit="1",
            description="Total number of failed login attempts by reason",
        )
        _counter_token_operations = _meter.create_counter(
            "token_operations_total",
            unit="1",
            description="Total number of token operations",
        )
        _histogram_token_generation_duration = _meter.create_histogram(
            "token_generation_duration_seconds",
            unit="s",
            description="Time spent generating tokens",
        )
        _histogram_token_expiration = _meter.create_histogram(
            "token_expiration_seconds",
            unit="s",
            description="Token expiration time distribution",
        )
        from opentelemetry.metrics import Observation

        def _observe_active_tokens(options: Any) -> None:
            for token_type, count in _gauge_active_tokens.items():
                yield Observation(count, _attrs(token_type=token_type))

        _meter.create_observable_gauge(
            "active_tokens",
            callbacks=[_observe_active_tokens],
            unit="1",
            description="Number of active tokens",
        )
        _updown_active_tokens = None  # Not used; we use observable gauge for set() semantics
        _counter_user_operations = _meter.create_counter(
            "user_operations_total",
            unit="1",
            description="Total number of user operations",
        )
        _histogram_user_registration_duration = _meter.create_histogram(
            "user_registration_duration_seconds",
            unit="s",
            description="Time spent processing user registration",
        )
        def _observe_total_users(options: Any) -> None:
            for status, count in _gauge_total_users.items():
                yield Observation(count, _attrs(status=status))

        _meter.create_observable_gauge(
            "total_users",
            callbacks=[_observe_total_users],
            unit="1",
            description="Total number of users in the system",
        )
        _updown_total_users = None  # Not used; we use observable gauge for set() semantics
        _counter_password_operations = _meter.create_counter(
            "password_operations_total",
            unit="1",
            description="Total number of password operations",
        )
        _histogram_password_strength = _meter.create_histogram(
            "password_strength_score",
            unit="1",
            description="Password strength score distribution",
        )
        _counter_role_operations = _meter.create_counter(
            "role_operations_total",
            unit="1",
            description="Total number of role operations",
        )
        _counter_permission_checks = _meter.create_counter(
            "permission_checks_total",
            unit="1",
            description="Total number of permission checks",
        )
        _histogram_permission_check_duration = _meter.create_histogram(
            "permission_check_duration_seconds",
            unit="s",
            description="Time spent checking permissions",
        )
        _updown_active_sessions = _meter.create_up_down_counter(
            "active_sessions",
            unit="1",
            description="Number of active user sessions",
        )
        _counter_session_operations = _meter.create_counter(
            "session_operations_total",
            unit="1",
            description="Total number of session operations",
        )
        _histogram_session_duration = _meter.create_histogram(
            "session_duration_seconds",
            unit="s",
            description="User session duration distribution",
        )
        _updown_database_connections = _meter.create_up_down_counter(
            "database_connections_active",
            unit="1",
            description="Number of active database connections",
        )
        _counter_database_operations = _meter.create_counter(
            "database_operations_total",
            unit="1",
            description="Total number of database operations",
        )
        _histogram_database_operation_duration = _meter.create_histogram(
            "database_operation_duration_seconds",
            unit="s",
            description="Duration of database operations",
        )
        _counter_application_errors = _meter.create_counter(
            "application_errors_total",
            unit="1",
            description="Total number of application errors",
        )
        _counter_security_events = _meter.create_counter(
            "security_events_total",
            unit="1",
            description="Total number of security events",
        )
        logger.info("Azure Monitor metrics initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Azure metrics: {e}", exc_info=True)
        raise


def _attrs(**kwargs: str) -> dict[str, str]:
    return {k: str(v) for k, v in kwargs.items() if v is not None}


def record_authentication_metrics(
    auth_type: str,
    duration: float,
    status: str,
    failure_reason: str | None = None,
) -> None:
    try:
        if _counter_authentication_attempts is None:
            return
        attrs = _attrs(auth_type=auth_type, status=status)
        _counter_authentication_attempts.add(1, attrs)
        _histogram_authentication_duration.record(duration, attrs)
        if status == "failure" and failure_reason:
            _counter_failed_login_attempts.add(1, _attrs(reason=failure_reason))
    except Exception as e:
        logger.error(f"Error recording authentication metrics: {e}")


def record_token_metrics(
    operation_type: str,
    token_type: str,
    duration: float,
    status: str,
    expiration_seconds: int | None = None,
) -> None:
    try:
        if _counter_token_operations is None:
            return
        attrs = _attrs(operation_type=operation_type, token_type=token_type, status=status)
        _counter_token_operations.add(1, attrs)
        if operation_type == "generate":
            _histogram_token_generation_duration.record(duration, _attrs(token_type=token_type))
            if expiration_seconds is not None:
                _histogram_token_expiration.record(
                    float(expiration_seconds), _attrs(token_type=token_type)
                )
    except Exception as e:
        logger.error(f"Error recording token metrics: {e}")


def record_user_operation_metrics(
    operation_type: str,
    duration: float,
    status: str,
) -> None:
    try:
        if _counter_user_operations is None:
            return
        attrs = _attrs(operation_type=operation_type, status=status)
        _counter_user_operations.add(1, attrs)
        if operation_type == "create":
            _histogram_user_registration_duration.record(duration, _attrs(status=status))
    except Exception as e:
        logger.error(f"Error recording user operation metrics: {e}")


def record_password_operation_metrics(
    operation_type: str,
    status: str,
    strength_score: int | None = None,
) -> None:
    try:
        if _counter_password_operations is None:
            return
        _counter_password_operations.add(1, _attrs(operation_type=operation_type, status=status))
        if strength_score is not None:
            _histogram_password_strength.record(float(strength_score))
    except Exception as e:
        logger.error(f"Error recording password operation metrics: {e}")


def record_permission_check_metrics(
    resource: str,
    action: str,
    result: str,
    duration: float,
) -> None:
    try:
        if _counter_permission_checks is None:
            return
        _counter_permission_checks.add(1, _attrs(resource=resource, action=action, result=result))
        _histogram_permission_check_duration.record(duration, _attrs(resource=resource))
    except Exception as e:
        logger.error(f"Error recording permission check metrics: {e}")


def record_database_metrics(
    operation_type: str,
    table: str,
    duration: float,
    status: str = "success",
) -> None:
    try:
        if _counter_database_operations is None:
            return
        _counter_database_operations.add(
            1, _attrs(operation_type=operation_type, table=table, status=status)
        )
        _histogram_database_operation_duration.record(
            duration, _attrs(operation_type=operation_type, table=table)
        )
    except Exception as e:
        logger.error(f"Error recording database metrics: {e}")


def database_connections_activating() -> None:
    try:
        if _updown_database_connections is not None:
            _updown_database_connections.add(1)
    except Exception as e:
        logger.error(f"Error recording database connection activation: {e}")


def database_connections_deactivating() -> None:
    try:
        if _updown_database_connections is not None:
            _updown_database_connections.add(-1)
    except Exception as e:
        logger.error(f"Error recording database connection deactivation: {e}")


def record_security_event(event_type: str, severity: str) -> None:
    try:
        if _counter_security_events is not None:
            _counter_security_events.add(1, _attrs(event_type=event_type, severity=severity))
    except Exception as e:
        logger.error(f"Error recording security event metrics: {e}")


def active_sessions_incrementing() -> None:
    try:
        if _updown_active_sessions is not None:
            _updown_active_sessions.add(1)
    except Exception as e:
        logger.error(f"Error incrementing active sessions: {e}")


def active_sessions_decrementing() -> None:
    try:
        if _updown_active_sessions is not None:
            _updown_active_sessions.add(-1)
    except Exception as e:
        logger.error(f"Error decrementing active sessions: {e}")


def update_active_tokens_gauge(token_type: str, count: int) -> None:
    """Update the active tokens gauge. Stored for compatibility; Azure uses UpDownCounter so we track delta in callers if needed."""
    try:
        if _updown_active_tokens is None:
            return
        # UpDownCounter doesn't have set(); we only use it for inc/dec elsewhere. This API was "set count".
        # Store for any future observable callback; for now we just keep the dict for API compatibility.
        _gauge_active_tokens[token_type] = count
    except Exception as e:
        logger.error(f"Error updating active tokens gauge: {e}")


def update_total_users_gauge(status: str, count: int) -> None:
    """Update the total users gauge. Stored for compatibility."""
    try:
        _gauge_total_users[status] = count
        if _updown_total_users is None:
            return
        # Same as above: UpDownCounter doesn't support set; keep for API compatibility.
    except Exception as e:
        logger.error(f"Error updating total users gauge: {e}")
