from datetime import datetime, timedelta, timezone
import jwt
from domain.entities.token_model import TokenPayload
from domain.entities.user_model import UserModel, UserWithRolesModel
from infrastructure.repositories.role_repository import RoleRepository
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.service_repository import ServiceRepository
from infrastructure.observability.metrics.decorators import track_token_operation
from infrastructure.observability.logging.decorators import log_token_operation_decorator
from infrastructure.observability.tracing.decorators import trace_token_operation


class TokenService:
    """Service for creating and validating JWT tokens"""
    
    def __init__(self, secret_key: str, algorithm: str, role_repo: RoleRepository, user_repo: UserRepository, service_repo: ServiceRepository):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.role_repo = role_repo
        self.user_repo = user_repo
        self.service_repo = service_repo
    
    @track_token_operation(operation_type='generate', token_type='access')
    @log_token_operation_decorator(operation_type='generate', token_type='access')
    @trace_token_operation(operation_type='generate', token_type='access')
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
        now = datetime.now(timezone.utc)
        
        if user.id is None:
            raise ValueError("Id cannot be null when creating a token")

        # Fetch user roles
        user_roles = await self.role_repo.get_user_roles(user)
        
        # Group roles by service
        roles_by_service: dict[str, list[str]] = {}
        for role in user_roles:
            service_id = str(role.service_id)
            service_model = await self.service_repo.get_by_id(role.service_id)
            if service_model is None:
                    raise Exception(f"No service found for service id : {service_id}")
            
            if service_id not in roles_by_service:
                roles_by_service[service_model.name] = []
            roles_by_service[service_model.name].append(role.name)
        
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

        return jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)
    
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
    
        


        