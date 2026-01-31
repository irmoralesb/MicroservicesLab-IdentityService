from infrastructure.repositories.user_repository import UserRepository
from domain.entities.user_model import UserModel
from domain.exceptions.auth_errors import AccountLockedError
from core.security import get_bcrypt_context
from datetime import datetime, timedelta, timezone
from infrastructure.observability.metrics.decorators import track_authentication, track_security_event
from infrastructure.observability.metrics.prometheus import record_security_event
from infrastructure.observability.logging.decorators import (
    log_authentication,
    log_security_event_decorator,
)
from infrastructure.observability.logging.loki_handler import (
    get_structured_logger,
    log_security_event,
)
from infrastructure.observability.tracing.decorators import (
    trace_authentication,
    trace_security_event,
)


class AuthenticateService():
    
    def __init__(self,max_failed_password_attempts: int,lockout_duration_in_minutes: int, user_repo: UserRepository):
        self.max_failed_password_attempts = max_failed_password_attempts
        self.lockout_duration_in_minutes = lockout_duration_in_minutes
        self.user_repo = user_repo

    @track_authentication(auth_type='login')
    @log_authentication(auth_type='login')
    @trace_authentication(auth_type='login')
    async def authenticate_user(self, email: str, password: str) -> UserModel | None:
        """
        Authenticate user with lockout mechanism.
        
        Args:
            email: User's email address
            password: User's plaintext password
            
        Returns:
            UserModel if authentication successful, None otherwise
            
        Raises:
            AccountLockedError: If account is temporarily locked
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            return None

        # Get current UTC time (timezone-aware)
        now_utc = datetime.now(timezone.utc)
        
        # Check if account is locked
        if user.locked_until:
            # Ensure locked_until is a datetime object and timezone-aware
            if isinstance(user.locked_until, str):
                # Parse string to datetime if needed
                from dateutil import parser
                locked_until_aware = parser.parse(user.locked_until)
            elif isinstance(user.locked_until, datetime):
                # If it's a datetime, ensure it's timezone-aware
                locked_until_aware = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until.tzinfo is None else user.locked_until
            else:
                # Fallback: assume it's already correct
                locked_until_aware = user.locked_until
            
            if locked_until_aware > now_utc:
                raise AccountLockedError(
                    locked_until=locked_until_aware.strftime("%Y-%m-%d %H:%M:%S UTC")
                )

        # Verify password
        if get_bcrypt_context().verify(password, user.hashed_password):
            # Successful login - reset failed attempts
            if user.failed_login_attempts > 0 or user.locked_until:
                user.failed_login_attempts = 0
                user.locked_until = None
                await self.user_repo.update_user(user)
            return user
        else:
            # Failed login - increment counter
            user.failed_login_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= self.max_failed_password_attempts:
                user.locked_until = now_utc + timedelta(
                    minutes=self.lockout_duration_in_minutes
                )
                # Record security event for account lockout
                record_security_event(
                    event_type='account_locked',
                    severity='medium'
                )
                 
                # Log security event with structured context
                logger = get_structured_logger("auth.security")
                log_security_event(
                    logger=logger,
                    event_type='account_locked',
                    severity='medium',
                    details=f'Email account: {email}'
                ) 
                
            await self.user_repo.update_user(user)
            return None

    @track_security_event(event_type='account_unlocked', severity='low')
    @log_security_event_decorator(event_type='account_unlocked',severity='low')
    @trace_security_event(event_type='account_unlocked', severity='low')
    async def unlock_account(self, user_id) -> bool:
        """
        Unlock a user account by resetting failed login attempts and lockout time.
        
        Args:
            user_id: UUID of the user account to unlock
            
        Returns:
            bool: True if unlock was successful
        """
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            return False
        
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.user_repo.update_user(user)
        
        return True