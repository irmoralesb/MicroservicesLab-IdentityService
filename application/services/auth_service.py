from infrastructure.repositories.user_repository import UserRepository
from domain.entities.user_model import UserModel
from core.security import get_bcrypt_context
from typing import Annotated


async def get_auth_service() -> AuthenticateService:
    return AuthenticateService()

class AuthenticateService():

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, email: str, password: str) -> UserModel | None:
        """Checks if the user password matches the stored hashed password"""
        user = await self.user_repo.get_by_email(email)

        if not user:
            return None

        return user if get_bcrypt_context().verify(password, user.hashed_password) else None