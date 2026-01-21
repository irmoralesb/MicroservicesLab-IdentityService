class CreateUserError(Exception):
    """Raised when the user can't be stored"""
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' cannot be created")

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