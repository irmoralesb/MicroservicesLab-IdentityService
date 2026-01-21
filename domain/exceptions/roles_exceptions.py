class RoleNotFound(Exception):
    """Raised when the role can't be found"""
    def __init__(self, role_name: str):
        self.role_name = role_name
        super().__init__(f"Role '{role_name}' cannot be found")

class AssignUserRoleError(Exception):
    def __init__(self, user_name:str, role_name:str):
        self.user_name = user_name
        self.role_name = role_name
        super().__init__(f"Error while assigning {role_name} role to {user_name}")
