import datetime
import uuid
from datetime import timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

from infrastructure.databases.database import Base


class UserDataModel(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(250), index=True, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0, nullable=False,
        comment="Number of consecutive failed login attempts")
    locked_until: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp until which the account is locked")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.getutcdate(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.getutcdate(), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)


class ServiceDataModel(Base):
    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint('name', name='uix_services_name'),
        Index('ix_services_name', 'name')
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Service name used for RBAC scoping")
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Service description")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Whether this service is active")
    url: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Base URL for the service")
    port: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Network port for the service")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.getutcdate(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.getutcdate(), nullable=False)


class RolesDataModel(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint('service_id', 'name', name='uix_service_role_name'),
        Index('ix_roles_service_id', 'service_id')
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
        index=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("services.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
        comment="Service identifier this role belongs to"
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Role name within the service (e.g., 'admin', 'user', 'translator')")
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Whether this role is currently active and can be assigned")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)


class PermissionsDataModel(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('service_id', 'resource', 'action',
                         name='uix_service_permission'),
        Index('ix_permission_service_id', 'service_id')
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    service_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("services.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
        comment="Service identifier this permission belongs to")
    name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Human-readable permission name")
    resource: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Resource type (e.g., 'user', 'translation', 'document')")
    action: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="Action type (e.g., 'create', 'read', 'update', 'delete')")
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)


class UserRolesDataModel(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uix_user_role'),
        Index('ix_user_role_user_id', 'user_id'),
        Index('ix_user_role_role_id', 'role_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False)
    assigned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)


class RolePermissionsDataModel(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id',
                         name='uix_role_permission'),
        Index('ix_role_permissions_role_id', 'role_id'),
        Index('ix_role_permissions_permission_id', 'permission_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False)
    assigned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)


class UserPermissionsDataModel(Base):
    __tablename__ = "user_permissions"
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id',
                         name='uix_user_permission'),
        Index('ix_user_permissions_user_id', 'user_id'),
        Index('ix_user_permissions_permission_id', 'permission_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False)
    assigned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=True,
        comment="Optional expiration for temporary permissions")


class RefreshTokensDataModel(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index('ix_refresh_tokens_user_id', 'user_id'),
        Index('ix_refresh_tokens_expires_at', 'expires_at'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True, index=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UNIQUEIDENTIFIER(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False)
    token_hashed: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=True)
