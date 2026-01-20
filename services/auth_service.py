from sqlalchemy.ext.asyncio import AsyncSession
from databases.models import UserDataModel
from sqlalchemy import select
from core.settings import app_settings
from core.security import get_bcrypt_context
from datetime import datetime, timedelta, timezone
from jose import jwt
import uuid


async def authenticate_user(email: str, password: str, db: AsyncSession) -> UserDataModel | None:
    """Checks if the user password matches the stored hashed password"""
    select_user_stmt = select(UserDataModel).where(
        UserDataModel.email == email)
    result = await db.execute(select_user_stmt)
    user = result.scalars().first()

    if not user:
        return None

    return user if get_bcrypt_context().verify(password, user.hashed_password) else None


def create_access_token(email: str, user_id: uuid.UUID, expires_delta: timedelta) -> str:
    encode = {'sub': email, 'user_id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, app_settings.secret_token_key, algorithm=app_settings.auth_algorithm)