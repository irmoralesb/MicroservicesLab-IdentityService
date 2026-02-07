from abc import ABC, abstractmethod
from typing import List
from domain.entities.user_model import UserModel
from uuid import UUID

class UserRepositoryInterface(ABC):
    """Abstract base class defining the interface for user repository operations."""

    @abstractmethod
    async def create_user(self, user: UserModel) -> UserModel:
        """
        Add a new user to the repository.

        Args:
            user: The user model to create

        Returns:
            UserModel: The created user with updated fields

        Raises:
            ValueError: If user data is invalid
            UserAlreadyExistsError: If a user with the same email already exists
        """
        pass

    @abstractmethod
    async def update_user(self, user: UserModel) -> UserModel:
        """
        Update an existing user in the repository.

        Args:
            user: The user model with updated fields

        Returns:
            UserModel: The updated user

        Raises:
            UserNotFoundError: If the user doesn't exist
            UserUpdateError: If the update operation fails
        """
        pass

    @abstractmethod
    async def soft_delete_user(self, user: UserModel) -> bool:
        """
        Soft delete an existing user in the repository.

        Args:
            user: The user model to soft delete

        Returns:
            bool: True if the user was soft deleted

        Raises:
            UserNotFoundError: If the user doesn't exist
            UserDeleteError: If the delete operation fails
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> UserModel | None:
        """
        Get a user by their email address.

        Args:
            email: The email address to search for

        Returns:
            UserModel | None: The user if found, None otherwise
        """
        pass


    @abstractmethod
    async def get_by_id(self, id: UUID) -> UserModel | None:
        """
        Get a user by their id.

        Args:
            id: The id to search for

        Returns:
            UserModel | None: The user if found, None otherwise
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists.

        Args:
            email: The email address to check

        Returns:
            bool: True if user exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_user_list(self) -> List[UserModel]:
        """
        Get all users in the application

        Returns:
            List[UserModel]: Returns the list of users in the application
        """
        pass
