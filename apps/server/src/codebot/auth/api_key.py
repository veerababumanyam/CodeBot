"""API key generation and hashing utilities."""

import hashlib
import secrets


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key with its hash and prefix.

    Returns:
        A tuple of (raw_key, sha256_hash, prefix_8_chars).
    """
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:8]
    return raw_key, key_hash, prefix


def hash_api_key(raw_key: str) -> str:
    """Hash a raw API key using SHA-256.

    Args:
        raw_key: The raw API key string.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()
