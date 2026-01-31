"""
Logging decorators for automatic operation instrumentation.

This module provides decorators for logging various domain operations with
structured context, following the same pattern as metrics decorators.

Pattern: Factory functions return decorators with specific configuration.
All decorators support async functions and wrap operations in try-except
blocks to prevent logging failures from breaking business logic.
"""

import time
from functools import wraps
from typing import Any, Callable
from uuid import UUID

from infrastructure.observability.logging.loki_handler import (
    get_structured_logger,
    log_authentication_event,
    log_authorization_check,
    log_database_operation,
    log_password_operation,
    log_security_event,
    log_token_operation,
    log_user_operation,
)


def log_operation(operation_type: str, log_level: str = "INFO"):
    """
    Generic decorator to log operation execution with context.

    Args:
        operation_type: Type of operation being performed
        log_level: Log level to use ('DEBUG', 'INFO', 'WARNING', 'ERROR')

    Returns:
        Decorator function

    Example:
        >>> @log_operation(operation_type='user_lookup', log_level='DEBUG')
        ... async def find_user_by_email(email: str) -> User:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger(func.__module__)
            start_time = time.perf_counter()

            # Log entry
            logger.log(
                getattr(__import__("logging"), log_level.upper()),
                f"Starting {operation_type}: {func.__name__}",
                extra={
                    "operation_type": operation_type,
                    "function": func.__name__,
                    "module": func.__module__,
                },
            )

            try:
                result = await func(*args, **kwargs)

                # Log success
                duration = time.perf_counter() - start_time
                logger.log(
                    getattr(__import__("logging"), log_level.upper()),
                    f"Completed {operation_type}: {func.__name__}",
                    extra={
                        "operation_type": operation_type,
                        "function": func.__name__,
                        "status": "success",
                        "duration_seconds": round(duration, 4),
                    },
                )

                return result

            except Exception as e:
                # Log failure
                duration = time.perf_counter() - start_time
                logger.error(
                    f"Failed {operation_type}: {func.__name__} - {str(e)}",
                    extra={
                        "operation_type": operation_type,
                        "function": func.__name__,
                        "status": "failure",
                        "duration_seconds": round(duration, 4),
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def log_authentication(auth_type: str):
    """
    Decorator to log authentication operations.

    Args:
        auth_type: Type of authentication ('login', 'refresh', 'verify')

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_authentication from metrics.
    Extracts user information from result and logs with structured context.

    Example:
        >>> @log_authentication(auth_type='login')
        ... async def authenticate_user(email: str, password: str) -> UserModel | None:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("auth")
            start_time = time.perf_counter()

            # Extract email from kwargs or args
            email = kwargs.get("email") or (args[1] if len(args) > 1 else None)

            try:
                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time

                # Determine success/failure based on result
                if result is None:
                    # Authentication failed
                    log_authentication_event(
                        logger=logger,
                        auth_type=auth_type,
                        status="failure",
                        email=email,
                        failure_reason="invalid_credentials",
                        duration_seconds=round(duration, 4),
                    )
                else:
                    # Authentication succeeded
                    user_id = getattr(result, "id", None)
                    log_authentication_event(
                        logger=logger,
                        auth_type=auth_type,
                        status="success",
                        user_id=user_id,
                        email=email,
                        duration_seconds=round(duration, 4),
                    )

                return result

            except Exception as e:
                # Authentication error
                duration = time.perf_counter() - start_time

                # Extract failure reason from exception type
                failure_reason = "error"
                if "AccountLockedError" in type(e).__name__:
                    failure_reason = "account_locked"
                elif "InvalidCredentialsError" in type(e).__name__:
                    failure_reason = "invalid_credentials"
                elif "ExpiredError" in type(e).__name__:
                    failure_reason = "expired"

                log_authentication_event(
                    logger=logger,
                    auth_type=auth_type,
                    status="failure",
                    email=email,
                    failure_reason=failure_reason,
                    duration_seconds=round(duration, 4),
                )

                raise

        return wrapper

    return decorator


def log_user_operation_decorator(operation_type: str):
    """
    Decorator to log user management operations.

    Args:
        operation_type: Type of operation ('create', 'update', 'delete', 'get', 'list')

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_user_operation from metrics.

    Example:
        >>> @log_user_operation_decorator(operation_type='create')
        ... async def create_user(user: UserModel) -> UserModel:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("user")
            start_time = time.perf_counter()

            # Extract user_id from kwargs if present
            user_id = kwargs.get("user_id")
            if not user_id and len(args) > 1:
                # Try to extract from first arg if it's a UUID
                if isinstance(args[1], UUID):
                    user_id = args[1]

            try:
                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time

                # Extract target_user_id from result if available
                target_user_id = None
                if hasattr(result, "id"):
                    target_user_id = result.id
                elif isinstance(result, dict) and "id" in result:
                    target_user_id = result["id"]

                log_user_operation(
                    logger=logger,
                    operation_type=operation_type,
                    status="success",
                    user_id=user_id,
                    target_user_id=target_user_id,
                    duration_seconds=round(duration, 4),
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                log_user_operation(
                    logger=logger,
                    operation_type=operation_type,
                    status="failure",
                    user_id=user_id,
                    duration_seconds=round(duration, 4),
                    error_message=str(e),
                )

                raise

        return wrapper

    return decorator


def log_password_operation_decorator(operation_type: str, record_security: bool = False):
    """
    Decorator to log password operations.

    Args:
        operation_type: Type of operation ('change', 'reset', 'validate', 'hash')
        record_security: Whether this operation should be marked as a security event

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_password_operation from metrics.

    Example:
        >>> @log_password_operation_decorator(operation_type='change', record_security=True)
        ... async def change_password(user_id: UUID, old_pwd: str, new_pwd: str) -> bool:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("password")
            start_time = time.perf_counter()

            # Extract user_id from kwargs or args
            user_id = kwargs.get("user_id") or (args[1] if len(args) > 1 and isinstance(args[1], UUID) else None)

            try:
                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time

                log_password_operation(
                    logger=logger,
                    operation_type=operation_type,
                    status="success",
                    user_id=user_id,
                    is_security_event=record_security,
                    duration_seconds=round(duration, 4),
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                log_password_operation(
                    logger=logger,
                    operation_type=operation_type,
                    status="failure",
                    user_id=user_id,
                    is_security_event=record_security,
                    duration_seconds=round(duration, 4),
                    error_message=str(e),
                )

                raise

        return wrapper

    return decorator


def log_token_operation_decorator(operation_type: str, token_type: str):
    """
    Decorator to log token operations.

    Args:
        operation_type: Type of operation ('generate', 'validate', 'revoke', 'refresh')
        token_type: Type of token ('access', 'refresh', 'reset')

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_token_operation from metrics.

    Example:
        >>> @log_token_operation_decorator(operation_type='generate', token_type='access')
        ... async def create_access_token(user: UserModel, expires_delta: timedelta) -> str:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("token")
            start_time = time.perf_counter()

            # Extract user_id and expires_delta from args/kwargs
            user = kwargs.get("user") or (args[1] if len(args) > 1 else None)
            user_id = getattr(user, "id", None) if user else None

            expires_delta = kwargs.get("expires_delta")
            expires_in_seconds = int(expires_delta.total_seconds()) if expires_delta else None

            try:
                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time

                log_token_operation(
                    logger=logger,
                    operation_type=operation_type,
                    token_type=token_type,
                    status="success",
                    user_id=user_id,
                    expires_in_seconds=expires_in_seconds,
                    duration_seconds=round(duration, 4),
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                log_token_operation(
                    logger=logger,
                    operation_type=operation_type,
                    token_type=token_type,
                    status="failure",
                    user_id=user_id,
                    expires_in_seconds=expires_in_seconds,
                    duration_seconds=round(duration, 4),
                    error_message=str(e),
                )

                raise

        return wrapper

    return decorator


def log_security_event_decorator(event_type: str, severity: str):
    """
    Decorator to log security events.

    Args:
        event_type: Type of security event ('account_locked', 'account_unlocked',
                   'suspicious_activity', 'unauthorized_access', etc.)
        severity: Severity level ('low', 'medium', 'high', 'critical')

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_security_event from metrics.

    Example:
        >>> @log_security_event_decorator(event_type='account_unlocked', severity='low')
        ... async def unlock_account(user_id: UUID) -> bool:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("security")

            # Extract user_id from kwargs or args
            user_id = kwargs.get("user_id") or (args[1] if len(args) > 1 and isinstance(args[1], UUID) else None)

            try:
                result = await func(*args, **kwargs)

                # Log security event on success
                log_security_event(
                    logger=logger,
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    details={"status": "success"},
                )

                return result

            except Exception as e:
                # Log security event on failure
                log_security_event(
                    logger=logger,
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    details={"status": "failure", "error": str(e)},
                )

                raise

        return wrapper

    return decorator


def log_database_operation_decorator(operation_type: str, entity_type: str):
    """
    Decorator to log database operations.

    Args:
        operation_type: Type of operation ('create', 'read', 'update', 'delete', 'query')
        entity_type: Type of entity ('user', 'role', 'token')

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_database_operation from metrics.

    Example:
        >>> @log_database_operation_decorator(operation_type='create', entity_type='user')
        ... async def create_user(user: UserModel) -> UserModel:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("database")
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time

                # Try to determine record count from result
                record_count = None
                if isinstance(result, list):
                    record_count = len(result)
                elif result is not None:
                    record_count = 1

                log_database_operation(
                    logger=logger,
                    operation_type=operation_type,
                    entity_type=entity_type,
                    status="success",
                    duration_seconds=round(duration, 4),
                    record_count=record_count,
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                log_database_operation(
                    logger=logger,
                    operation_type=operation_type,
                    entity_type=entity_type,
                    status="failure",
                    duration_seconds=round(duration, 4),
                    error_message=str(e),
                )

                raise

        return wrapper

    return decorator


def log_authorization_decorator():
    """
    Decorator to log authorization checks.

    Returns:
        Decorator function

    Pattern: Follows the same structure as track_authorization from metrics.
    Extracts required_roles and user information from function arguments.

    Example:
        >>> @log_authorization_decorator()
        ... async def authorize(user_id: UUID, required_roles: list[str]) -> bool:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_structured_logger("authorization")
            start_time = time.perf_counter()

            # Extract user_id and required_roles from kwargs
            user_id = kwargs.get("user_id")
            required_roles = kwargs.get("required_roles", [])
            resource = kwargs.get("resource")

            try:
                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time

                # Extract user roles if available from context
                user_roles = kwargs.get("user_roles", [])

                log_authorization_check(
                    logger=logger,
                    user_id=user_id,
                    required_roles=required_roles,
                    user_roles=user_roles,
                    is_authorized=bool(result),
                    resource=resource,
                    duration_seconds=round(duration, 4),
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                # Log as denied on exception
                log_authorization_check(
                    logger=logger,
                    user_id=user_id,
                    required_roles=required_roles,
                    user_roles=[],
                    is_authorized=False,
                    resource=resource,
                    duration_seconds=round(duration, 4),
                )

                raise

        return wrapper

    return decorator
