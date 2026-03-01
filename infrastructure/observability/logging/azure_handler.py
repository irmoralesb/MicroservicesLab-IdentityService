"""
Azure Monitor logging handler and structured logging utilities.

This module provides centralized Azure Monitor (Application Insights) handler
configuration, structured logger factory functions, and helper functions for
logging domain-specific events with rich context metadata.

Pattern: Same public API as the previous Loki handler for drop-in replacement.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

# Module logger for internal errors
_internal_logger = logging.getLogger(__name__)

# LoggerProvider and handler are set by setup_azure_handler
_logger_provider = None


def setup_azure_handler(
    connection_string: str,
    log_level: str = "INFO",
    batch_delay_millis: int = 60000,
):
    """
    Configure Azure Monitor logging and return a handler to attach to the root logger.

    Args:
        connection_string: Application Insights connection string
        log_level: Minimum log level to send (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        batch_delay_millis: Batch export delay in milliseconds

    Returns:
        LoggingHandler instance to add to root logger

    Example:
        >>> handler = setup_azure_handler(connection_string="...", log_level="INFO")
        >>> logging.getLogger().addHandler(handler)
    """
    global _logger_provider
    try:
        from opentelemetry._logs import set_logger_provider, get_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter

        _logger_provider = LoggerProvider()
        set_logger_provider(_logger_provider)
        exporter = AzureMonitorLogExporter.from_connection_string(connection_string)
        get_logger_provider().add_log_record_processor(
            BatchLogRecordProcessor(exporter, schedule_delay_millis=batch_delay_millis)
        )
        handler = LoggingHandler()
        handler.setLevel(getattr(logging, log_level.upper()))
        return handler
    except Exception as e:
        _internal_logger.error(f"Failed to setup Azure logging: {e}", exc_info=True)
        raise


def get_structured_logger(name: str, extra_labels: dict[str, str] | None = None) -> logging.Logger:
    """
    Get a logger instance configured for structured logging with optional custom labels.

    Args:
        name: Logger name (typically __name__ from calling module)
        extra_labels: Additional labels specific to this logger instance (stored on logger for reference)

    Returns:
        Logger instance with structured logging capabilities
    """
    logger = logging.getLogger(name)
    if extra_labels:
        if not hasattr(logger, "extra_labels"):
            logger.extra_labels = {}  # type: ignore
        logger.extra_labels.update(extra_labels)  # type: ignore
    return logger


def enrich_log_context(
    base_context: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Enrich log context with additional metadata, handling type conversions.
    """
    enriched = {**base_context}
    for key, value in kwargs.items():
        if value is None:
            enriched[key] = None
        elif isinstance(value, UUID):
            enriched[key] = str(value)
        elif isinstance(value, datetime):
            enriched[key] = value.isoformat()
        elif isinstance(value, (int, float, bool)):
            enriched[key] = value
        else:
            enriched[key] = str(value)
    return enriched


# ============================================================================
# Domain-specific structured logging helper functions
# ============================================================================


def log_authentication_event(
    logger: logging.Logger,
    auth_type: str,
    status: str,
    user_id: UUID | None = None,
    email: str | None = None,
    failure_reason: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    """Log authentication events with structured context."""
    try:
        message = f"Authentication {status}: {auth_type}"
        context = enrich_log_context(
            {
                "event_type": "authentication",
                "auth_type": auth_type,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            user_id=user_id,
            email=_mask_email(email) if email else None,
            failure_reason=failure_reason,
            duration_seconds=duration_seconds,
        )
        if status == "success":
            logger.info(message, extra=context)
        else:
            logger.warning(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log authentication event: {e}")


def log_user_operation(
    logger: logging.Logger,
    operation_type: str,
    status: str,
    user_id: UUID | None = None,
    target_user_id: UUID | None = None,
    duration_seconds: float | None = None,
    error_message: str | None = None,
) -> None:
    """Log user management operations with structured context."""
    try:
        message = f"User operation {status}: {operation_type}"
        context = enrich_log_context(
            {
                "event_type": "user_operation",
                "operation_type": operation_type,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            user_id=user_id,
            target_user_id=target_user_id,
            duration_seconds=duration_seconds,
            error_message=error_message,
        )
        if status == "success":
            logger.info(message, extra=context)
        else:
            logger.error(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log user operation: {e}")


def log_password_operation(
    logger: logging.Logger,
    operation_type: str,
    status: str,
    user_id: UUID | None = None,
    is_security_event: bool = False,
    duration_seconds: float | None = None,
    error_message: str | None = None,
) -> None:
    """Log password-related operations with structured context."""
    try:
        message = f"Password operation {status}: {operation_type}"
        context = enrich_log_context(
            {
                "event_type": "password_operation",
                "operation_type": operation_type,
                "status": status,
                "is_security_event": is_security_event,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            user_id=user_id,
            duration_seconds=duration_seconds,
            error_message=error_message,
        )
        if status == "success":
            if is_security_event:
                logger.warning(message, extra=context)
            else:
                logger.info(message, extra=context)
        else:
            logger.error(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log password operation: {e}")


def log_token_operation(
    logger: logging.Logger,
    operation_type: str,
    token_type: str,
    status: str,
    user_id: UUID | None = None,
    expires_in_seconds: int | None = None,
    duration_seconds: float | None = None,
    error_message: str | None = None,
) -> None:
    """Log token operations with structured context."""
    try:
        message = f"Token operation {status}: {operation_type} ({token_type})"
        context = enrich_log_context(
            {
                "event_type": "token_operation",
                "operation_type": operation_type,
                "token_type": token_type,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            user_id=user_id,
            expires_in_seconds=expires_in_seconds,
            duration_seconds=duration_seconds,
            error_message=error_message,
        )
        if status == "success":
            logger.info(message, extra=context)
        else:
            logger.error(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log token operation: {e}")


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    severity: str,
    user_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Log security-related events with structured context."""
    try:
        message = f"Security event [{severity.upper()}]: {event_type}"
        context = enrich_log_context(
            {
                "event_type": "security",
                "security_event_type": event_type,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            user_id=user_id,
            **(details or {}),
        )
        if severity == "critical":
            logger.critical(message, extra=context)
        elif severity == "high":
            logger.error(message, extra=context)
        elif severity == "medium":
            logger.warning(message, extra=context)
        else:
            logger.info(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log security event: {e}")


def log_database_operation(
    logger: logging.Logger,
    operation_type: str,
    entity_type: str,
    status: str,
    duration_seconds: float | None = None,
    record_count: int | None = None,
    error_message: str | None = None,
) -> None:
    """Log database operations with structured context."""
    try:
        message = f"Database operation {status}: {operation_type} ({entity_type})"
        context = enrich_log_context(
            {
                "event_type": "database_operation",
                "operation_type": operation_type,
                "entity_type": entity_type,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            duration_seconds=duration_seconds,
            record_count=record_count,
            error_message=error_message,
        )
        if status == "success":
            logger.debug(message, extra=context)
        else:
            logger.error(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log database operation: {e}")


def log_authorization_check(
    logger: logging.Logger,
    user_id: UUID,
    required_roles: list[str],
    user_roles: list[str],
    is_authorized: bool,
    resource: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    """Log authorization checks with structured context."""
    try:
        status = "granted" if is_authorized else "denied"
        message = f"Authorization {status}"
        context = enrich_log_context(
            {
                "event_type": "authorization",
                "status": status,
                "required_roles": required_roles,
                "user_roles": user_roles,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            user_id=user_id,
            resource=resource,
            duration_seconds=duration_seconds,
        )
        if is_authorized:
            logger.info(message, extra=context)
        else:
            logger.warning(message, extra=context)
    except Exception as e:
        _internal_logger.error(f"Failed to log authorization check: {e}")


def _mask_email(email: str) -> str:
    """Mask email address for privacy."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    masked_local = local[0] + "***" if len(local) > 1 else "*"
    return f"{masked_local}@{domain}"
