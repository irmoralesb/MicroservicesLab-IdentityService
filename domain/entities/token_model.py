from dataclasses import dataclass
from uuid import UUID
import datetime


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    sub: UUID  # User ID
    email: str
    roles: dict[str, list[str]]  # service_name -> list of roles
    exp: datetime.datetime
    iat: datetime.datetime
    
    
@dataclass
class TokenResponse:
    """Token response returned to clients"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds