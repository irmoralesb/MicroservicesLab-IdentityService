"""
Tracing decorators for automatic span creation and instrumentation.

This module provides decorator functions that automatically create and enrich
OpenTelemetry spans for various domain operations, following the same patterns
as the metrics and logging decorators.

Pattern:
--------
- Factory functions return configured decorators
- All decorators support async functions
- Automatic timing and error recording
- Wrapped in try-except to prevent tracing failures from breaking business logic

Usage:
------
    from infrastructure.observability.tracing.decorators import trace_authentication

    @trace_authentication(auth_type='login')
    async def authenticate_user(email: str, password: str) -> UserModel:
        # implementation
"""

import time
from functools import wraps
from typing import Any, Callable
from uuid import UUID

from opentelemetry.trace import Status, StatusCode

from infrastructure.observability.tracing.tempo import (
    get_tracer,
    enrich_authentication_span,
    enrich_authorization_span,
    enrich_database_operation_span,
    enrich_password_operation_span,
    enrich_security_event_span,
    enrich_token_operation_span,
    enrich_user_operation_span,
)


def trace_authentication(auth_type: str):
    """
    Decorator to trace authentication operations with automatic span creation.

    Creates a span for the authentication operation and enriches it with
    authentication-specific attributes. Automatically records timing and
    error information.

    Args:
        auth_type: Type of authentication ('login', 'refresh', 'verify')

    Returns:
        Decorator function

    Example:
        >>> @trace_authentication(auth_type='login')
        ... async def authenticate_user(email: str, password: str) -> UserModel | None:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"auth.{auth_type}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    # Extract email from args/kwargs for context
                    email = kwargs.get("email") or (args[1] if len(args) > 1 else None)

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        # Determine success/failure based on result
                        if result is None:
                            # None result indicates failed authentication
                            enrich_authentication_span(
                                span=span,
                                auth_type=auth_type,
                                status="failure",
                                email=email,
                                failure_reason="invalid_credentials",
                                duration_seconds=round(duration, 4),
                            )
                        else:
                            # Successful authentication
                            user_id = getattr(result, "id", None)
                            enrich_authentication_span(
                                span=span,
                                auth_type=auth_type,
                                status="success",
                                user_id=user_id,
                                email=email,
                                duration_seconds=round(duration, 4),
                            )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        # Record exception in span
                        span.record_exception(e)
                        enrich_authentication_span(
                            span=span,
                            auth_type=auth_type,
                            status="error",
                            email=email,
                            failure_reason=type(e).__name__,
                            duration_seconds=round(duration, 4),
                        )
                        raise

            except Exception as e:
                # Catch tracing setup errors to prevent breaking business logic
                # The inner try-except handles business logic exceptions
                # This outer catch is only for tracer.start_as_current_span errors
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_user_operation(operation_type: str):
    """
    Decorator to trace user management operations.

    Args:
        operation_type: Type of operation ('create', 'update', 'delete', 'get', 'list')

    Returns:
        Decorator function

    Example:
        >>> @trace_user_operation(operation_type='create')
        ... async def create_user(user: UserModel) -> UserModel:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"user.{operation_type}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    # Try to extract user_id from args/kwargs
                    user_id = kwargs.get("user_id")
                    if not user_id and len(args) > 0:
                        # Check if first arg has 'id' attribute (UserModel instance)
                        first_arg = args[0]
                        if hasattr(first_arg, "id"):
                            user_id = first_arg.id

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        # Try to get target user ID from result
                        target_user_id = None
                        if result and hasattr(result, "id"):
                            target_user_id = result.id

                        enrich_user_operation_span(
                            span=span,
                            operation_type=operation_type,
                            status="success",
                            user_id=user_id,
                            target_user_id=target_user_id,
                            duration_seconds=round(duration, 4),
                        )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        span.record_exception(e)
                        enrich_user_operation_span(
                            span=span,
                            operation_type=operation_type,
                            status="failure",
                            user_id=user_id,
                            duration_seconds=round(duration, 4),
                        )
                        raise

            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_password_operation(operation_type: str, record_security: bool = False):
    """
    Decorator to trace password operations.

    Args:
        operation_type: Type of operation ('change', 'reset', 'validate', 'hash')
        record_security: Whether this operation should be marked as a security event

    Returns:
        Decorator function

    Example:
        >>> @trace_password_operation(operation_type='change', record_security=True)
        ... async def change_password(user_id: UUID, old: str, new: str) -> bool:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"password.{operation_type}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    # Extract user_id from kwargs or args
                    user_id = kwargs.get("user_id")
                    if not user_id and len(args) > 1:
                        # For methods, args[0] is self, args[1] might be user_id
                        potential_id = args[1] if len(args) > 1 else None
                        if isinstance(potential_id, UUID):
                            user_id = potential_id

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        enrich_password_operation_span(
                            span=span,
                            operation_type=operation_type,
                            status="success",
                            user_id=user_id,
                            is_security_event=record_security,
                            duration_seconds=round(duration, 4),
                        )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        span.record_exception(e)
                        enrich_password_operation_span(
                            span=span,
                            operation_type=operation_type,
                            status="failure",
                            user_id=user_id,
                            is_security_event=record_security,
                            duration_seconds=round(duration, 4),
                        )
                        raise

            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_token_operation(operation_type: str, token_type: str):
    """
    Decorator to trace token operations.

    Args:
        operation_type: Type of operation ('generate', 'validate', 'refresh', 'revoke')
        token_type: Type of token ('access', 'refresh')

    Returns:
        Decorator function

    Example:
        >>> @trace_token_operation(operation_type='generate', token_type='access')
        ... async def create_access_token(user: UserModel) -> str:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"token.{operation_type}.{token_type}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    # Try to extract user or user_id
                    user_id = kwargs.get("user_id")
                    user = kwargs.get("user")
                    if not user_id and user and hasattr(user, "id"):
                        user_id = user.id

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        enrich_token_operation_span(
                            span=span,
                            operation_type=operation_type,
                            token_type=token_type,
                            status="success",
                            user_id=user_id,
                            duration_seconds=round(duration, 4),
                        )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        span.record_exception(e)
                        enrich_token_operation_span(
                            span=span,
                            operation_type=operation_type,
                            token_type=token_type,
                            status="failure",
                            user_id=user_id,
                            duration_seconds=round(duration, 4),
                        )
                        raise

            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_database_operation(operation_type: str, table: str):
    """
    Decorator to trace database operations.

    Args:
        operation_type: Type of operation ('select', 'insert', 'update', 'delete')
        table: Database table name

    Returns:
        Decorator function

    Example:
        >>> @trace_database_operation(operation_type='insert', table='users')
        ... async def create_user_in_db(user: UserModel) -> UserModel:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"db.{operation_type}.{table}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        enrich_database_operation_span(
                            span=span,
                            operation_type=operation_type,
                            table=table,
                            status="success",
                            duration_seconds=round(duration, 4),
                        )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        span.record_exception(e)
                        enrich_database_operation_span(
                            span=span,
                            operation_type=operation_type,
                            table=table,
                            status="failure",
                            duration_seconds=round(duration, 4),
                        )
                        raise

            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_authorization(resource: str, action: str):
    """
    Decorator to trace authorization checks.

    Args:
        resource: Resource being accessed
        action: Action being performed

    Returns:
        Decorator function

    Example:
        >>> @trace_authorization(resource='user', action='delete')
        ... async def check_delete_permission(user: UserModel) -> bool:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"authz.{resource}.{action}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    # Extract user information from kwargs
                    user_id = kwargs.get("user_id")
                    user = kwargs.get("user")
                    if not user_id and user:
                        if hasattr(user, "id"):
                            user_id = user.id
                        elif hasattr(user, "user") and hasattr(user.user, "id"):
                            user_id = user.user.id

                    required_roles = kwargs.get("required_roles", [])
                    user_roles = kwargs.get("user_roles", [])

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        is_authorized = bool(result)

                        enrich_authorization_span(
                            span=span,
                            resource=resource,
                            action=action,
                            is_authorized=is_authorized,
                            user_id=user_id,
                            required_roles=required_roles,
                            user_roles=user_roles,
                            duration_seconds=round(duration, 4),
                        )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        span.record_exception(e)
                        enrich_authorization_span(
                            span=span,
                            resource=resource,
                            action=action,
                            is_authorized=False,
                            user_id=user_id,
                            required_roles=required_roles,
                            user_roles=user_roles,
                            duration_seconds=round(duration, 4),
                        )
                        raise

            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_security_event(event_type: str, severity: str):
    """
    Decorator to trace security events.

    Args:
        event_type: Type of security event (account_locked, suspicious_activity, etc.)
        severity: Event severity (low, medium, high, critical)

    Returns:
        Decorator function

    Example:
        >>> @trace_security_event(event_type='account_locked', severity='medium')
        ... async def lock_account(user_id: UUID) -> bool:
        ...     # implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = f"security.{event_type}.{func.__name__}"

            try:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    start_time = time.perf_counter()

                    # Extract user_id
                    user_id = kwargs.get("user_id")
                    if not user_id and len(args) > 1:
                        potential_id = args[1] if len(args) > 1 else None
                        if isinstance(potential_id, UUID):
                            user_id = potential_id

                    try:
                        result = await func(*args, **kwargs)
                        duration = time.perf_counter() - start_time

                        enrich_security_event_span(
                            span=span,
                            event_type=event_type,
                            severity=severity,
                            user_id=user_id,
                            details={"duration_seconds": round(duration, 4)},
                        )

                        return result

                    except Exception as e:
                        duration = time.perf_counter() - start_time

                        span.record_exception(e)
                        enrich_security_event_span(
                            span=span,
                            event_type=event_type,
                            severity=severity,
                            user_id=user_id,
                            details={
                                "duration_seconds": round(duration, 4),
                                "error": type(e).__name__,
                            },
                        )
                        raise

            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
