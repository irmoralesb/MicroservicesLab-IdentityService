from uuid import UUID


class PermissionNotFoundError(Exception):
    """Raised when the permission can't be found."""

    def __init__(self, permission_id: str | UUID):
        self.permission_id = permission_id
        super().__init__(f"Permission '{permission_id}' cannot be found")


class PermissionCreationError(Exception):
    """Raised when a permission cannot be created."""

    def __init__(self, permission_name: str | None) -> None:
        self.permission_name = permission_name
        super().__init__(f"Error creating permission {permission_name}")


class PermissionUpdateError(Exception):
    """Raised when a permission update fails."""

    def __init__(self, permission_id: UUID) -> None:
        self.permission_id = permission_id
        super().__init__(f"Error updating permission {permission_id}")


class PermissionDeleteError(Exception):
    """Raised when a permission deletion fails."""

    def __init__(self, permission_id: UUID) -> None:
        self.permission_id = permission_id
        super().__init__(f"Error deleting permission {permission_id}")


class PermissionStillAssignedError(Exception):
    """Raised when attempting to delete a permission that is still assigned to roles."""

    def __init__(self, permission_id: UUID) -> None:
        self.permission_id = permission_id
        super().__init__(
            f"Cannot delete permission {permission_id} because it is still assigned to one or more roles"
        )

class PermissionReadError(Exception):
    """Raised when a read attempt fails"""

    def __init__(self, message:str) -> None:
        self.message = message
        super().__init__(message)
