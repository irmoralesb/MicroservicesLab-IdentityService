"""
Decorator functions for automatic Prometheus metrics instrumentation.
These decorators provide a clean, DRY approach to metrics collection.
"""
from functools import wraps
import time
from typing import Callable, Any
from datetime import timedelta
from domain.exceptions.auth_errors import AccountLockedError, PasswordChangeError
from infrastructure.observability.metrics.prometheus import (
    record_authentication_metrics,
    record_security_event,
    record_user_operation_metrics,
    record_password_operation_metrics,
    record_token_metrics,
    record_database_metrics,
    record_permission_check_metrics
)


def track_authentication(auth_type: str):
    """
    Decorator to track authentication operations with automatic metrics recording.
    
    Args:
        auth_type: Type of authentication ('login', 'refresh', 'verify')
    
    Handles:
        - Timing measurement
        - Success/failure status tracking
        - Failure reason extraction from exceptions
        - Security event recording for account lockouts
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = None
            
            try:
                result = await func(*args, **kwargs)
                
                # Check if authentication was successful
                if result is None:
                    duration = time.perf_counter() - start_time
                    record_authentication_metrics(
                        auth_type=auth_type,
                        duration=duration,
                        status='failure',
                        failure_reason='invalid_credentials'
                    )
                else:
                    duration = time.perf_counter() - start_time
                    record_authentication_metrics(
                        auth_type=auth_type,
                        duration=duration,
                        status='success'
                    )
                
                return result
            except AccountLockedError:
                duration = time.perf_counter() - start_time
                record_authentication_metrics(
                    auth_type=auth_type,
                    duration=duration,
                    status='failure',
                    failure_reason='account_locked'
                )
                raise
            except Exception:
                duration = time.perf_counter() - start_time
                record_authentication_metrics(
                    auth_type=auth_type,
                    duration=duration,
                    status='failure',
                    failure_reason='error'
                )
                raise
        
        return wrapper
    return decorator


def track_user_operation(operation_type: str):
    """
    Decorator to track user management operations.
    
    Args:
        operation_type: Type of operation ('create', 'update', 'delete', 'activate', 'deactivate')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                record_user_operation_metrics(
                    operation_type=operation_type,
                    duration=duration,
                    status='success'
                )
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                record_user_operation_metrics(
                    operation_type=operation_type,
                    duration=duration,
                    status='failure'
                )
                raise
        
        return wrapper
    return decorator


def track_password_operation(operation_type: str, record_security: bool = True):
    """
    Decorator to track password operations.
    
    Args:
        operation_type: Type of operation ('change', 'reset', 'validate')
        record_security: Whether to record a security event on success
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                record_password_operation_metrics(
                    operation_type=operation_type,
                    status='success'
                )
                
                if record_security:
                    record_security_event(
                        event_type='password_changed',
                        severity='low'
                    )
                
                return result
            except (PasswordChangeError, Exception):
                record_password_operation_metrics(
                    operation_type=operation_type,
                    status='failure'
                )
                raise
        
        return wrapper
    return decorator


def track_token_operation(operation_type: str, token_type: str):
    """
    Decorator to track token operations.
    
    Args:
        operation_type: Type of operation ('generate', 'validate', 'revoke', 'refresh')
        token_type: Type of token ('access', 'refresh')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                # Try to extract expiration info from kwargs if this is token generation
                expiration_seconds = None
                if operation_type == 'generate' and 'expires_delta' in kwargs:
                    expires_delta = kwargs['expires_delta']
                    if isinstance(expires_delta, timedelta):
                        expiration_seconds = int(expires_delta.total_seconds())
                
                record_token_metrics(
                    operation_type=operation_type,
                    token_type=token_type,
                    duration=duration,
                    status='success',
                    expiration_seconds=expiration_seconds
                )
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                record_token_metrics(
                    operation_type=operation_type,
                    token_type=token_type,
                    duration=duration,
                    status='failure'
                )
                raise
        
        return wrapper
    return decorator


def track_database_operation(operation_type: str, table: str):
    """
    Decorator to track database operations.
    
    Args:
        operation_type: Type of operation ('insert', 'update', 'select', 'delete')
        table: Table name
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                record_database_metrics(
                    operation_type=operation_type,
                    table=table,
                    duration=duration,
                    status='success'
                )
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                record_database_metrics(
                    operation_type=operation_type,
                    table=table,
                    duration=duration,
                    status='error'
                )
                raise
        
        return wrapper
    return decorator


def track_permission_check(resource: str, action: str):
    """
    Decorator to track permission checks.
    
    Args:
        resource: Resource being accessed
        action: Action being performed
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                # Result is boolean indicating permission granted/denied
                record_permission_check_metrics(
                    resource=resource,
                    action=action,
                    result='allowed' if result else 'denied',
                    duration=duration
                )
                
                # Still record database metrics
                record_database_metrics(
                    operation_type='select',
                    table='permissions',
                    duration=duration,
                    status='success'
                )
                
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                record_database_metrics(
                    operation_type='select',
                    table='permissions',
                    duration=duration,
                    status='error'
                )
                raise
        
        return wrapper
    return decorator


def track_security_event(event_type: str, severity: str):
    """
    Decorator to record security events after successful execution.
    
    Args:
        event_type: Type of security event ('account_locked', 'account_unlocked', etc.)
        severity: Event severity ('low', 'medium', 'high', 'critical')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)
            
            # Only record event if operation was successful
            if result:
                record_security_event(
                    event_type=event_type,
                    severity=severity
                )
            
            return result
        
        return wrapper
    return decorator
