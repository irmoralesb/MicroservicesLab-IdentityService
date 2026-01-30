class RoleNotFoundError(Exception):
    """Raised when the role can't be found"""
    def __init__(self, role_name: str):
        self.role_name = role_name
        super().__init__(f"Role '{role_name}' cannot be found")

class AssignUserRoleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
