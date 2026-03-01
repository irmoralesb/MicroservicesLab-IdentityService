"""
Azure Monitor distributed tracing setup and helper functions.

This module provides OpenTelemetry tracer configuration for distributed tracing
with Azure Monitor (Application Insights), with the same public API as the
previous Tempo-based setup.
"""

import logging
import socket
from datetime import datetime
from typing import Any
from uuid import UUID

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Status, StatusCode, Tracer

_internal_logger = logging.getLogger(__name__)


def setup_azure_tracer(
    connection_string: str,
    service_name: str,
    sample_rate: float = 1.0,
    enable_console_export: bool = False,
) -> TracerProvider:
    """
    Configure and return OpenTelemetry TracerProvider for Azure Monitor.

    Args:
        connection_string: Application Insights connection string
        service_name: Name of this service for trace identification
        sample_rate: Sampling rate between 0.0 and 1.0 (1.0 = 100% of traces)
        enable_console_export: If True, also export traces to console for debugging

    Returns:
        TracerProvider: Configured tracer provider instance
    """
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

        resource = Resource.create(
            attributes={
                ResourceAttributes.SERVICE_NAME: str(service_name),
                ResourceAttributes.SERVICE_VERSION: "1.0.0",
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development",
                ResourceAttributes.HOST_NAME: socket.gethostname(),
            }
        )
        sampler = TraceIdRatioBased(sample_rate)
        provider = TracerProvider(resource=resource, sampler=sampler)

        azure_exporter = AzureMonitorTraceExporter.from_connection_string(connection_string)
        provider.add_span_processor(BatchSpanProcessor(azure_exporter))

        if enable_console_export:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))

        trace.set_tracer_provider(provider)
        _internal_logger.info(
            f"Azure tracer configured: service={service_name}, sample_rate={sample_rate}"
        )
        return provider
    except Exception as e:
        _internal_logger.error(f"Failed to setup Azure tracer: {e}", exc_info=True)
        raise


def get_tracer(name: str) -> Tracer:
    """Get a tracer instance for a module or component."""
    return trace.get_tracer(name)


def _safe_str(value: Any) -> str:
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
    """Enrich span with authentication-specific attributes."""
    try:
        span.set_attribute("auth.type", auth_type)
        span.set_attribute("auth.status", status)
        if user_id is not None:
            span.set_attribute("user.id", str(user_id))
        if email is not None:
            parts = email.split("@")
            masked = f"***@{parts[1]}" if len(parts) == 2 else "***"
            span.set_attribute("user.email", masked)
        if failure_reason is not None:
            span.set_attribute("auth.failure_reason", failure_reason)
        if duration_seconds is not None:
            span.set_attribute("auth.duration_seconds", duration_seconds)
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
    """Enrich span with user operation-specific attributes."""
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
    """Enrich span with password operation-specific attributes."""
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
    """Enrich span with token operation-specific attributes."""
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
    """Enrich span with database operation-specific attributes."""
    try:
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
    """Enrich span with authorization check-specific attributes."""
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
    """Enrich span with security event-specific attributes."""
    try:
        span.set_attribute("security.event.type", event_type)
        span.set_attribute("security.event.severity", severity)
        if user_id is not None:
            span.set_attribute("user.id", str(user_id))
        if details:
            for key, value in details.items():
                span.set_attribute(f"security.event.{key}", _safe_str(value))
        if severity in ("high", "critical"):
            span.set_status(Status(StatusCode.ERROR, description=f"Security event: {event_type}"))
        else:
            span.set_status(Status(StatusCode.OK))
    except Exception as e:
        _internal_logger.error(f"Failed to enrich security event span: {e}")
