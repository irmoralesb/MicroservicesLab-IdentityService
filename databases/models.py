from sqlalchemy import String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from databases.database import Base
import uuid
import datetime


class UserDataModel(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), index=True, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.getutcdate(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.getutcdate(), nullable=False)


class RolesDataModel(Base):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)


class PermissionsDataModel(Base):
    __tablename__ = "permissions"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    resource: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)


class UserRolesDataModel(Base):
    __tablename__ = "user_roles"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("roles.id"), nullable=False)


class RolePermissionsDataModel(Base):
    __tablename__ = "role_permissions"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("permissions.id"), nullable=False)


class UserPermissionsDataModel(Base):
    __tablename__ = "user_permissions"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("permissions.id"), nullable=False)


class RefreshTokensDataModel(Base):
    __tablename__ = "refresh_token"
    id: Mapped[uuid.UUID] = mapped_column(
        String(36), default=uuid.uuid4,
        primary_key=True, index=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False)
    token_hashed: Mapped[str] = mapped_column(String)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
