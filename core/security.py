import hashlib
import secrets
from typing import Optional

from core.config import settings


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed


def anonymize_text(text: str, user_id: Optional[int] = None) -> str:
    """
    Anonymize text by removing PII.

    This is a placeholder implementation.
    In production, use a more sophisticated NLP-based approach.
    """
    # Remove telegram IDs, phone numbers, etc.
    anonymized = text

    # Replace user mentions
    if user_id:
        anonymized = anonymized.replace(str(user_id), "[USER]")

    # TODO: Implement more sophisticated PII removal
    # - Phone numbers
    # - Email addresses
    # - Names (NER)
    # - Location data

    return anonymized
