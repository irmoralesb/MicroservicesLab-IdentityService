from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.role_repository import RoleRepository
from domain.entities.user_model import UserModel
from domain.entities.role_model import RoleModel
from domain.exceptions.auth_exceptions import UserCreationError


class UserService:
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo


    async def create_user_with_default_role(self, user: UserModel, default_role_name: str) -> UserModel:
        """
        Create a new user and assign them the default role

        Args:
            user: User entity to create
            default_role_name: Name of the default role to assign

        Returns:
            Created user entity

        Raises:
            UserCreationError: If user creation or role assignment fails
        """
        user_default_role: RoleModel = await self.role_repo.get_by_name(default_role_name)
        new_user: UserModel = await self.user_repo.create_user(user)

        is_success = bool = await self.role_repo.assign_role(new_user, user_default_role)

        if not is_success:
            raise UserCreationError("Failed to assign default role to user")
        
        return new_user