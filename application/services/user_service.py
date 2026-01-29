from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.role_repository import RoleRepository
from domain.entities.user_model import UserModel
from domain.entities.role_model import RoleModel
from domain.exceptions.auth_exceptions import UserCreationError, PasswordChangeError
from core.security import get_bcrypt_context
from core.password_validator import PasswordValidator, PasswordValidationError
from uuid import UUID


class UserService:
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        """
        Initialize the UserService with required repositories.

        Args:
            user_repo: Repository for user data operations
            role_repo: Repository for role data operations
        """
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

    # TODO: VALIDATE WHAT CALLER HAS PERMISSION
    async def get_user_profile(self, user_id: UUID) -> UserModel | None:
        """
        Retrieve a user's profile by their ID.

        Args:
            user_id: UUID of the user to retrieve

        Returns:
            UserModel | None: The user profile if found, None otherwise
        """
        user_data = await self.user_repo.get_by_id(user_id)
        return None if user_data is None else user_data

    async def update_user_profile(self, user: UserModel) -> UserModel:
        """
        Update an existing user's profile information.

        Args:
            user: User entity with updated information

        Returns:
            UserModel: The updated user entity

        Raises:
            UserNotFoundException: If the user doesn't exist
            UserUpdateError: If the update operation fails
        """
        return await self.user_repo.update_user(user)

    async def activate_user(self, user_id: UUID) -> bool:
        """
        Activate a user account by setting is_active to True.

        Args:
            user_id: UUID of the user to activate

        Returns:
            bool: True if activation was successful

        Raises:
            UserNotFoundException: If the user doesn't exist
            UserUpdateError: If the update operation fails
        """
        user_data = await self.user_repo.get_by_id(user_id)
        user_data.is_active = True
        await self.user_repo.update_user(user_data)
        return True
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate a user account by setting is_active to False
        
        Args:
            user_id: UUID of the user to deacticate

        Returns:
            bool: True if deactivation was successful
        """
        user_data = await self.user_repo.get_by_id(user_id)
        user_data.is_active = False
        await self.user_repo.update_user(user_data)
        return True

    async def change_password(
        self, 
        user_id: UUID, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change a user's password after validating current password and new password requirements.
        
        Args:
            user_id: UUID of the user changing password
            current_password: User's current password for verification
            new_password: New password to set
            
        Returns:
            bool: True if password change was successful
            
        Raises:
            PasswordChangeError: If current password is incorrect or user not found
            PasswordValidationError: If new password doesn't meet requirements
        """
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise PasswordChangeError("User not found")
        
        # Verify current password
        if not get_bcrypt_context().verify(current_password, user.hashed_password):
            raise PasswordChangeError("Current password is incorrect")
        
        # Validate new password
        PasswordValidator.validate(new_password)
        
        # Hash and set new password
        user.hashed_password = get_bcrypt_context().hash(new_password)
        await self.user_repo.update_user(user)
        
        return True

