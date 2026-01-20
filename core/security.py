from passlib.context import CryptContext

_bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_bcrypt_context() -> CryptContext:
    """Dependency to provide bcrypt context for password hashing."""
    return _bcrypt_context
