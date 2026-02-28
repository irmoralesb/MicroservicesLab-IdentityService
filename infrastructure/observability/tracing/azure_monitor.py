"""
Azure Monitor tracing setup and helper functions.

This module provides OpenTelemetry tracer configuration for distributed tracing
with Azure Monitor (Application Insights), replacing the former Grafana Tempo
integration.  The ``configure_azure_monitor`` distro (called in ``main.py``)
handles exporter wiring; this module only needs to call
``opentelemetry.trace.get_tracer()`` to obtain a configured tracer.

Pattern:
--------
- Centralized tracer accessors
- Domain-specific span enrichment functions  (unchanged from the Tempo era —
  they use the standard OpenTelemetry Span API)
- Type-safe attribute handling
- All operations wrapped in try-except to prevent failures
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from opentelemetry import trace
from opentelemetry.sdk.trace import Span
from opentelemetry.trace import Status, StatusCode, Tracer

# Internal logger for this module
_internal_logger = logging.getLogger(__name__)


def get_tracer(name: str) -> Tracer:
    """
    Get a tracer instance for a module or component.

    Args:
        name: Name for the tracer (typically __name__ from calling module)

    Returns:
        Tracer: OpenTelemetry tracer instance
    """
    return trace.get_tracer(name)


def _safe_str(value: Any) -> str:
    """Safely convert value to string, handling None and special types."""
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
            span.set_status(
                Status(StatusCode.ERROR, description=failure_reason or "Authentication failed")
            )
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
                safe_value = _safe_str(value)
                span.set_attribute(f"security.event.{key}", safe_value)

        if severity in ("high", "critical"):
            span.set_status(Status(StatusCode.ERROR, description=f"Security event: {event_type}"))
        else:
            span.set_status(Status(StatusCode.OK))
    except Exception as e:
        _internal_logger.error(f"Failed to enrich security event span: {e}")
