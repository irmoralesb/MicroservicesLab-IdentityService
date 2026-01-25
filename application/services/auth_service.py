from infrastructure.repositories.user_repository import UserRepository
from domain.entities.user_model import UserModel
from core.security import get_bcrypt_context


class AuthenticateService():


    async def authenticate_user(self, email: str, password: str, user_repo: UserRepository) -> UserModel | None:
        """Checks if the user password matches the stored hashed password"""
        user = await user_repo.get_by_email(email)

        if not user:
            return None

        return user if get_bcrypt_context().verify(password, user.hashed_password) else None