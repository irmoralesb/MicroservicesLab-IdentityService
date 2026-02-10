from uuid import UUID


class RoleNotFoundError(Exception):
    """Raised when the role can't be found."""

    def __init__(self, role_name: str | UUID):
        self.role_name = role_name
        super().__init__(f"Role '{role_name}' cannot be found")


class RoleCreationError(Exception):
    """Raised when a role cannot be created."""

    def __init__(self, role_name: str | None) -> None:
        self.role_name = role_name
        super().__init__(f"Error creating role {role_name}")


class RoleUpdateError(Exception):
    """Raised when a role update fails."""

    def __init__(self, role_id: UUID) -> None:
        self.role_id = role_id
        super().__init__(f"Error updating role {role_id}")


class RoleDeleteError(Exception):
    """Raised when a role deletion fails."""

    def __init__(self, role_id: UUID) -> None:
        self.role_id = role_id
        super().__init__(f"Error deleting role {role_id}")


class RoleListError(Exception):
    """Raised when role listing fails."""

    def __init__(self, service_id: UUID) -> None:
        self.service_id = service_id
        super().__init__(f"Error fetching roles for service {service_id}")


class AssignUserRoleError(Exception):
    """Raised when assigning a role to a user fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UnassignUserRoleError(Exception):
    """Raised when unassigning a role from a user fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
