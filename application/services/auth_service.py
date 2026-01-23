from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt
from infrastructure.repositories.user_repository import UserRepository
from domain.entities.user_model import UserModel
from core.security import get_bcrypt_context
#from core.settings import app_settings


class AuthenticateService():


    async def authenticate_user(self, email: str, password: str, user_repo: UserRepository) -> UserModel | None:
        """Checks if the user password matches the stored hashed password"""
        user = await user_repo.get_by_email(email)

        if not user:
            return None

        return user if get_bcrypt_context().verify(password, user.hashed_password) else None


    # def create_access_token(self, email: str, user_id: uuid.UUID, expires_delta: timedelta) -> str:
    #     encode = {'sub': email, 'user_id': user_id}
    #     expires = datetime.now(timezone.utc) + expires_delta
    #     encode.update({'exp': expires})
    #     return jwt.encode(encode, app_settings.secret_token_key, algorithm=app_settings.auth_algorithm)