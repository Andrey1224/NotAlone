import hashlib
import hmac
import secrets

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


def anonymize_text(text: str, user_id: int | None = None) -> str:
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


def generate_callback_hmac(match_id: int, user_id: int) -> str:
    """
    Generate HMAC signature for callback data to prevent tampering.

    Args:
        match_id: Match ID
        user_id: User ID making the action

    Returns:
        Hex-encoded HMAC signature (first 8 chars for brevity)
    """
    message = f"{match_id}:{user_id}"
    signature = hmac.new(settings.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return signature[:8]  # Truncate for callback_data size limits


def verify_callback_hmac(match_id: int, user_id: int, provided_hmac: str) -> bool:
    """
    Verify HMAC signature for callback data.

    Args:
        match_id: Match ID
        user_id: User ID making the action
        provided_hmac: HMAC signature from callback_data

    Returns:
        True if signature is valid
    """
    expected_hmac = generate_callback_hmac(match_id, user_id)
    return hmac.compare_digest(expected_hmac, provided_hmac)
