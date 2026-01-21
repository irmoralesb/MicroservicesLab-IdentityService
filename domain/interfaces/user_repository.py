from abc import ABC, abstractmethod
from domain.entities.user_model import UserModel


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
            UserAlreadyExistsException: If a user with the same email already exists
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
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists.

        Args:
            email: The email address to check

        Returns:
            bool: True if user exists, False otherwise
        """
        pass
