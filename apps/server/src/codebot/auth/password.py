"""Password hashing and verification using bcrypt."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password.

    Returns:
        Bcrypt hash string.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        password: The plaintext password to check.
        hashed: The bcrypt hash to verify against.

    Returns:
        True if the password matches the hash.
    """
    return bcrypt.checkpw(password.encode(), hashed.encode())
