"""
Grafana Tempo tracing setup and helper functions.

This module provides OpenTelemetry tracer configuration for distributed tracing
with Grafana Tempo, following the same patterns as Loki and Prometheus setup.

Pattern:
--------
- Centralized tracer configuration
- Domain-specific span enrichment functions
- Type-safe attribute handling
- All operations wrapped in try-except to prevent failures

Usage:
------
    from infrastructure.observability.tracing.tempo import setup_tempo_tracer, get_tracer

    # At application startup
    tracer_provider = setup_tempo_tracer(
        endpoint="http://localhost:4317",
        service_name="identity-service",
        sample_rate=1.0
    )

    # In application code
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("operation_name") as span:
        span.set_attribute("key", "value")
"""

import logging
import socket
from datetime import datetime
from typing import Any
from uuid import UUID

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Status, StatusCode, Tracer

# Internal logger for this module (not sent to Loki to avoid circular dependencies)
_internal_logger = logging.getLogger(__name__)


def setup_tempo_tracer(
    endpoint: str,
    service_name: str,
    sample_rate: float = 1.0,
    enable_console_export: bool = False,
) -> TracerProvider:
    """
    Configure and return OpenTelemetry TracerProvider for Grafana Tempo.

    This function sets up the global tracer provider with OTLP exporter
    configured to send traces to Grafana Tempo. It follows the same pattern
    as setup_loki_handler for consistency.

    Args:
        endpoint: Tempo OTLP gRPC endpoint URL (e.g., "http://localhost:4317")
        service_name: Name of this service for trace identification
        sample_rate: Sampling rate between 0.0 and 1.0 (1.0 = 100% of traces)
        enable_console_export: If True, also export traces to console for debugging

    Returns:
        TracerProvider: Configured tracer provider instance

    Raises:
        Exception: If tracer setup fails (should be caught by caller)

    Example:
        >>> provider = setup_tempo_tracer(
        ...     endpoint="http://localhost:4317",
        ...     service_name="identity-service",
        ...     sample_rate=1.0
        ... )
    """
    try:
        # Create resource with service identification
        resource = Resource.create(
            attributes={
                ResourceAttributes.SERVICE_NAME: service_name,
                ResourceAttributes.SERVICE_VERSION: "1.0.0",
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development",
                ResourceAttributes.HOST_NAME: socket.gethostname(),
            }
        )

        # Create sampler based on sample rate
        sampler = TraceIdRatioBased(sample_rate)

        # Create tracer provider
        provider = TracerProvider(
            resource=resource,
            sampler=sampler,
        )

        # Configure OTLP exporter for Tempo
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=True,  # Use insecure connection for development
        )

        # Add batch span processor with OTLP exporter
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Optionally add console exporter for debugging
        if enable_console_export:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        _internal_logger.info(
            f"Tempo tracer configured: endpoint={endpoint}, "
            f"service={service_name}, sample_rate={sample_rate}"
        )

        return provider

    except Exception as e:
        _internal_logger.error(f"Failed to setup Tempo tracer: {e}", exc_info=True)
        raise


def get_tracer(name: str) -> Tracer:
    """
    Get a tracer instance for a module or component.

    This function provides a consistent way to get tracer instances across
    the application, similar to get_structured_logger for logging.

    Args:
        name: Name for the tracer (typically __name__ from calling module)

    Returns:
        Tracer: OpenTelemetry tracer instance

    Example:
        >>> tracer = get_tracer(__name__)
        >>> with tracer.start_as_current_span("operation"):
        ...     # operation code
    """
    return trace.get_tracer(name)


def _safe_str(value: Any) -> str:
    """
    Safely convert value to string, handling None and special types.

    Args:
        value: Value to convert

    Returns:
        String representation of value
    """
    if value is None:
        return "None"
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def enrich_authentication_span(
    span: Span,
    auth_type: str,
    status: str,
    user_id: UUID | None = None,
    email: str | None = None,
    failure_reason: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    """
    Enrich span with authentication-specific attributes.

    Follows OpenTelemetry semantic conventions where applicable and
    adds custom attributes for domain-specific context.

    Args:
        span: Active span to enrich
        auth_type: Type of authentication operation (login, refresh, verify)
        status: Operation status (success, failure)
        user_id: Optional user identifier
        email: Optional user email (will be masked in logs)
        failure_reason: Optional reason for failure
        duration_seconds: Optional operation duration

    Example:
        >>> with tracer.start_as_current_span("authenticate") as span:
        ...     enrich_authentication_span(
        ...         span, auth_type="login", status="success", user_id=user.id
        ...     )
    """
    try:
        # Set standard attributes
        span.set_attribute("auth.type", auth_type)
        span.set_attribute("auth.status", status)

        # Set optional attributes
        if user_id is not None:
            span.set_attribute("user.id", str(user_id))

        if email is not None:
            # Mask email for privacy (show only domain)
            parts = email.split("@")
            masked = f"***@{parts[1]}" if len(parts) == 2 else "***"
            span.set_attribute("user.email", masked)

        if failure_reason is not None:
            span.set_attribute("auth.failure_reason", failure_reason)

        if duration_seconds is not None:
            span.set_attribute("auth.duration_seconds", duration_seconds)

        # Set span status based on operation status
        if status == "success":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description=failure_reason or "Authentication failed"))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich authentication span: {e}")


def enrich_user_operation_span(
    span: Span,
    operation_type: str,
    status: str,
    user_id: UUID | None = None,
    target_user_id: UUID | None = None,
    duration_seconds: float | None = None,
) -> None:
    """
    Enrich span with user operation-specific attributes.

    Args:
        span: Active span to enrich
        operation_type: Type of operation (create, update, delete, get, list)
        status: Operation status (success, failure)
        user_id: Optional ID of user performing the operation
        target_user_id: Optional ID of user being operated on
        duration_seconds: Optional operation duration
    """
    try:
        span.set_attribute("user.operation.type", operation_type)
        span.set_attribute("user.operation.status", status)

        if user_id is not None:
            span.set_attribute("user.actor.id", str(user_id))

        if target_user_id is not None:
            span.set_attribute("user.target.id", str(target_user_id))

        if duration_seconds is not None:
            span.set_attribute("user.operation.duration_seconds", duration_seconds)

        if status == "success":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description="User operation failed"))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich user operation span: {e}")


def enrich_password_operation_span(
    span: Span,
    operation_type: str,
    status: str,
    user_id: UUID | None = None,
    is_security_event: bool = False,
    duration_seconds: float | None = None,
) -> None:
    """
    Enrich span with password operation-specific attributes.

    Args:
        span: Active span to enrich
        operation_type: Type of operation (change, reset, validate, hash)
        status: Operation status (success, failure)
        user_id: Optional user identifier
        is_security_event: Whether this is a security-relevant event
        duration_seconds: Optional operation duration
    """
    try:
        span.set_attribute("password.operation.type", operation_type)
        span.set_attribute("password.operation.status", status)
        span.set_attribute("password.is_security_event", is_security_event)

        if user_id is not None:
            span.set_attribute("user.id", str(user_id))

        if duration_seconds is not None:
            span.set_attribute("password.operation.duration_seconds", duration_seconds)

        if status == "success":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description="Password operation failed"))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich password operation span: {e}")


def enrich_token_operation_span(
    span: Span,
    operation_type: str,
    token_type: str,
    status: str,
    user_id: UUID | None = None,
    duration_seconds: float | None = None,
) -> None:
    """
    Enrich span with token operation-specific attributes.

    Args:
        span: Active span to enrich
        operation_type: Type of operation (generate, validate, refresh, revoke)
        token_type: Type of token (access, refresh)
        status: Operation status (success, failure)
        user_id: Optional user identifier
        duration_seconds: Optional operation duration
    """
    try:
        span.set_attribute("token.operation.type", operation_type)
        span.set_attribute("token.type", token_type)
        span.set_attribute("token.operation.status", status)

        if user_id is not None:
            span.set_attribute("user.id", str(user_id))

        if duration_seconds is not None:
            span.set_attribute("token.operation.duration_seconds", duration_seconds)

        if status == "success":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description="Token operation failed"))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich token operation span: {e}")


def enrich_database_operation_span(
    span: Span,
    operation_type: str,
    table: str,
    status: str,
    duration_seconds: float | None = None,
) -> None:
    """
    Enrich span with database operation-specific attributes.

    Follows OpenTelemetry database semantic conventions.

    Args:
        span: Active span to enrich
        operation_type: Type of operation (select, insert, update, delete)
        table: Database table name
        status: Operation status (success, failure)
        duration_seconds: Optional operation duration
    """
    try:
        # Use OpenTelemetry semantic conventions for database operations
        span.set_attribute("db.operation", operation_type)
        span.set_attribute("db.sql.table", table)
        span.set_attribute("db.system", "mssql")
        span.set_attribute("db.operation.status", status)

        if duration_seconds is not None:
            span.set_attribute("db.operation.duration_seconds", duration_seconds)

        if status == "success":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description="Database operation failed"))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich database operation span: {e}")


def enrich_authorization_span(
    span: Span,
    resource: str,
    action: str,
    is_authorized: bool,
    user_id: UUID | None = None,
    required_roles: list[str] | None = None,
    user_roles: list[str] | None = None,
    duration_seconds: float | None = None,
) -> None:
    """
    Enrich span with authorization check-specific attributes.

    Args:
        span: Active span to enrich
        resource: Resource being accessed
        action: Action being performed
        is_authorized: Whether authorization was granted
        user_id: Optional user identifier
        required_roles: Optional list of required roles
        user_roles: Optional list of user's roles
        duration_seconds: Optional operation duration
    """
    try:
        span.set_attribute("authz.resource", resource)
        span.set_attribute("authz.action", action)
        span.set_attribute("authz.granted", is_authorized)

        if user_id is not None:
            span.set_attribute("user.id", str(user_id))

        if required_roles:
            span.set_attribute("authz.required_roles", ",".join(required_roles))

        if user_roles:
            span.set_attribute("authz.user_roles", ",".join(user_roles))

        if duration_seconds is not None:
            span.set_attribute("authz.duration_seconds", duration_seconds)

        if is_authorized:
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, description="Authorization denied"))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich authorization span: {e}")


def enrich_security_event_span(
    span: Span,
    event_type: str,
    severity: str,
    user_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Enrich span with security event-specific attributes.

    Args:
        span: Active span to enrich
        event_type: Type of security event (account_locked, suspicious_activity, etc.)
        severity: Event severity (low, medium, high, critical)
        user_id: Optional user identifier
        details: Optional additional event details
    """
    try:
        span.set_attribute("security.event.type", event_type)
        span.set_attribute("security.event.severity", severity)

        if user_id is not None:
            span.set_attribute("user.id", str(user_id))

        if details:
            for key, value in details.items():
                safe_value = _safe_str(value)
                span.set_attribute(f"security.event.{key}", safe_value)

        # Security events are always important, set appropriate status
        if severity in ("high", "critical"):
            span.set_status(Status(StatusCode.ERROR, description=f"Security event: {event_type}"))
        else:
            span.set_status(Status(StatusCode.OK))

    except Exception as e:
        _internal_logger.error(f"Failed to enrich security event span: {e}")
