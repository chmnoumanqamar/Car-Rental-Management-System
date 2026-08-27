"""
Security and Authentication Utilities
Implements salted PBKDF2-HMAC-SHA256 password hashing and verification.
"""

import hashlib
import secrets

def hash_password(password: str) -> str:
    """
    Hashes a plain text password with a unique cryptographic salt.
    Returns format: salt$hash
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verifies a provided plaintext password against a stored salt$hash string.
    """
    if not stored_password or not provided_password:
        return False
    
    try:
        if "$" not in stored_password:
            # Fallback for plain SHA256 if applicable
            return False
        
        salt, expected_hash = stored_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(key.hex(), expected_hash)
    except Exception:
        return False
