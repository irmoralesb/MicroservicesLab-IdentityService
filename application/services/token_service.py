from uuid import UUID
from datetime import datetime, timedelta, timezone
import jwt
from domain.entities.token_model import TokenPayload
from domain.entities.user_model import UserModelWithRoles


class TokenService:
    """Service for creating and validating JWT tokens"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(
        self,
        user_with_roles: UserModelWithRoles,
        expires_delta: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Create JWT access token with user roles grouped by service
        
        Args:
            user_with_roles: User entity with their roles
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)
        
        if user_with_roles.user.id is None:
            raise ValueError("Id cannot be null when creating a token")

        # Group roles by service (assuming RoleModel has service_name attribute)
        roles_by_service: dict[str, list[str]] = {}
        for role in user_with_roles.roles:
            service = role.service  # e.g., "identity-service", "translation-service"
            if service not in roles_by_service:
                roles_by_service[service] = []
            roles_by_service[service].append(role.name)
        
        payload = TokenPayload(
            sub=user_with_roles.user.id,
            email=user_with_roles.user.email,
            roles=roles_by_service,
            exp=now + expires_delta,
            iat=now
        )
        
        # Convert to dict for JWT encoding
        token_data = {
            "sub": str(payload.sub),
            "email": payload.email,
            "roles": payload.roles,
            "exp": payload.exp,
            "iat": payload.iat
        }

        # PyJWT 2.x returns str, but type checker might see bytes
        return jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)     # pyright: ignore[reportReturnType]
