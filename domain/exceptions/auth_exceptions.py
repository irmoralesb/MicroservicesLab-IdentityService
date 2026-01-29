class UserCreationError(Exception):
    """Raised when the user can't be stored"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' cannot be created")


class UserUpdateError(Exception):
    """Raised when the user can't be updated"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' cannot be updated")


class UserAlreadyExistsException(Exception):
    """Raised when a user already exists in the database"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' already exists")


class UserNotFoundException(Exception):
    """Raised when a user is not found"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' not found")


class UnauthorizedUserException(Exception):
    """Raised when a user is not authorized to perform an action"""

    def __init__(self, message: str = "User is not authorized to perform this action"):
        self.message = message
        super().__init__(self.message)


class InactiveUserException(Exception):
    """Raised when a user account is inactive"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User account '{email}' is not active")


class MissingRoleException(Exception):
    """Raised when a user doesn't have required role"""

    def __init__(self, role_name: str):
        self.role_name = role_name
        super().__init__(f"User does not have required role: '{role_name}'")


class MissingPermissionException(Exception):
    """Raised when a user doesn't have required permission"""

    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action
        super().__init__(
            f"User does not have permission to {action} {resource}")


class AccountLockedException(Exception):
    """Raised when a user account is temporarily locked due to failed login attempts"""

    def __init__(self, locked_until: str):
        self.locked_until = locked_until
        super().__init__(
            f"Account is temporarily locked. Please try again after {locked_until}")


class InvalidPasswordException(Exception):
    """Raised when password does not meet security requirements"""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class PasswordChangeError(Exception):
    """Raised when password change operation fails"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
