"""
Password validation service for enforcing strong password policies.
"""
import re
from typing import List


class PasswordValidationError(Exception):
    """Raised when password validation fails"""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class PasswordValidator:
    """
    Validates passwords against security requirements.
    
    Requirements:
    - Minimum length: 8 characters
    - Maximum length: 100 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """

    MIN_LENGTH = 8
    MAX_LENGTH = 100
    SPECIAL_CHARACTERS = r"[!@#$%^&*(),.?\":{}|<>[\]\\\/`~;'_\-+=]"

    @classmethod
    def validate(cls, password: str) -> None:
        """
        Validate password against all requirements.
        
        Args:
            password: Password string to validate
            
        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        errors: List[str] = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if not re.search(cls.SPECIAL_CHARACTERS, password):
            errors.append("Password must contain at least one special character")

        if errors:
            raise PasswordValidationError(errors)

    @classmethod
    def is_valid(cls, password: str) -> bool:
        """
        Check if password is valid without raising exception.
        
        Args:
            password: Password string to validate
            
        Returns:
            bool: True if password is valid, False otherwise
        """
        try:
            cls.validate(password)
            return True
        except PasswordValidationError:
            return False
