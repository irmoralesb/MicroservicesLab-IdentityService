"""
Azure Monitor logging handler and structured logging utilities.

This module provides centralized logging configuration for Azure Monitor
(Application Insights / Log Analytics).  The ``configure_azure_monitor``
distro automatically captures Python ``logging`` records and exports them
to Application Insights, so the helpers here simply emit log records with
rich structured context — no custom handler wiring is needed.

Pattern: Follows the same centralized definition pattern as the former
loki_handler.py to avoid duplication and ensure consistent logging across
the application.
"""

import logging
import socket
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

# Module logger for internal errors
_internal_logger = logging.getLogger(__name__)


def setup_azure_log_handler(
    log_level: str = "INFO",
) -> None:
    """
    Configure the root logger level for Azure Monitor export.

    The actual Azure Monitor exporter is wired by ``configure_azure_monitor``
    in ``main.py``.  This helper exists to keep the initialisation interface
    consistent with the rest of the application.

    Args:
        log_level: Minimum log level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))


def get_structured_logger(
    name: str, extra_labels: dict[str, str] | None = None
) -> logging.Logger:
    """
    Get a logger instance configured for structured logging with optional custom labels.

    Args:
        name: Logger name (typically __name__ from calling module)
        extra_labels: Additional labels specific to this logger instance

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

    Args:
        base_context: Base context dictionary
        **kwargs: Additional key-value pairs to add to context

    Returns:
        Enriched context dictionary with proper type conversions
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
    """
    Log authentication events with structured context.

    Args:
        logger: Logger instance to use
        auth_type: Type of authentication ('login', 'refresh', 'verify')
        status: Authentication status ('success', 'failure')
        user_id: User ID if authentication succeeded
        email: User email (masked for privacy)
        failure_reason: Reason for failure if status is 'failure'
        duration_seconds: Time taken for authentication operation
    """
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
    """
    Log user management operations with structured context.

    Args:
        logger: Logger instance to use
        operation_type: Type of operation ('create', 'update', 'delete', 'get', 'list')
        status: Operation status ('success', 'failure')
        user_id: ID of user performing the operation
        target_user_id: ID of user being operated on
        duration_seconds: Time taken for operation
        error_message: Error message if operation failed
    """
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
    """
    Log password-related operations with structured context.

    Args:
        logger: Logger instance to use
        operation_type: Type of operation ('change', 'reset', 'validate', 'hash')
        status: Operation status ('success', 'failure')
        user_id: ID of user whose password is being operated on
        is_security_event: Whether this is a security-relevant event
        duration_seconds: Time taken for operation
        error_message: Error message if operation failed
    """
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
    """
    Log token operations with structured context.

    Args:
        logger: Logger instance to use
        operation_type: Type of operation ('generate', 'validate', 'revoke', 'refresh')
        token_type: Type of token ('access', 'refresh', 'reset')
        status: Operation status ('success', 'failure')
        user_id: ID of user the token belongs to
        expires_in_seconds: Token expiration time in seconds
        duration_seconds: Time taken for operation
        error_message: Error message if operation failed
    """
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
    """
    Log security-related events with structured context.

    Args:
        logger: Logger instance to use
        event_type: Type of security event ('account_locked', 'account_unlocked',
                   'suspicious_activity', 'unauthorized_access', etc.)
        severity: Severity level ('low', 'medium', 'high', 'critical')
        user_id: ID of user involved in the security event
        details: Additional event-specific details
    """
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

        # Map severity to log level
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
    """
    Log database operations with structured context.

    Args:
        logger: Logger instance to use
        operation_type: Type of operation ('create', 'read', 'update', 'delete', 'query')
        entity_type: Type of entity being operated on ('user', 'role', 'token')
        status: Operation status ('success', 'failure')
        duration_seconds: Time taken for operation
        record_count: Number of records affected/returned
        error_message: Error message if operation failed
    """
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
    """
    Log authorization checks with structured context.

    Args:
        logger: Logger instance to use
        user_id: ID of user being authorized
        required_roles: Roles required for access
        user_roles: Roles the user has
        is_authorized: Whether authorization succeeded
        resource: Resource being accessed (optional)
        duration_seconds: Time taken for authorization check
    """
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


# ============================================================================
# Utility functions
# ============================================================================


def _mask_email(email: str) -> str:
    """
    Mask email address for privacy while keeping it identifiable.

    Args:
        email: Email address to mask

    Returns:
        Masked email (e.g., j***@example.com)
    """
    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)

    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "***"

    return f"{masked_local}@{domain}"
