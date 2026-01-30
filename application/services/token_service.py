from datetime import datetime, timedelta, timezone
import jwt
from domain.entities.token_model import TokenPayload
from domain.entities.user_model import UserModel, UserWithRolesModel
from infrastructure.repositories.role_repository import RoleRepository
from infrastructure.repositories.user_repository import UserRepository
import time
from infrastructure.observability.metrics.prometheus import record_token_metrics


class TokenService:
    """Service for creating and validating JWT tokens"""
    
    def __init__(self, secret_key: str, algorithm: str, role_repo: RoleRepository, user_repo: UserRepository):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.role_repo = role_repo
        self.user_repo = user_repo
    
    async def create_access_token(
        self,
        user: UserModel,
        expires_delta: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Create JWT access token with user roles grouped by service
        
        Args:
            user: User entity
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token string
        """
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)
        
        if user.id is None:
            raise ValueError("Id cannot be null when creating a token")

        # Fetch user roles
        user_roles = await self.role_repo.get_user_roles(user)
        
        # Group roles by service
        roles_by_service: dict[str, list[str]] = {}
        for role in user_roles:
            service = role.service
            if service not in roles_by_service:
                roles_by_service[service] = []
            roles_by_service[service].append(role.name)
        
        payload = TokenPayload(
            sub=user.id,
            email=user.email,
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

        token = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)
        
        # Record token generation metrics
        duration = time.perf_counter() - start_time
        expiration_seconds = int(expires_delta.total_seconds())
        record_token_metrics(
            operation_type='generate',
            token_type='access',
            duration=duration,
            status='success',
            expiration_seconds=expiration_seconds
        )
        
        return token
    
    async def get_user(self, token: str) -> UserWithRolesModel:
        
        payload = jwt.decode(token, self.secret_key, self.algorithm)
        user_id = payload.get('sub')
        user = await self.user_repo.get_by_id(user_id)

        if user is None:
            raise ValueError(
                "Cannot read the user data")
        
        roles = await self.role_repo.get_user_roles(user)

        if roles is None or len(roles) == 0:
            raise ValueError(
                "Cannot read the user roles")

        user_with_roles = UserWithRolesModel(user,roles)
        return user_with_roles
    
        


        