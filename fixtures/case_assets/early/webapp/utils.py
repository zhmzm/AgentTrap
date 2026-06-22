"""Utility functions."""
import hashlib
import re


def hash_password(password: str) -> str:
    # BUG 5: MD5 used for password hashing — should use bcrypt or argon2
    return hashlib.md5(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Return True if email looks valid."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def sanitize_input(text: str) -> str:
    """Remove HTML tags from input."""
    return re.sub(r"<[^>]+>", "", text)
