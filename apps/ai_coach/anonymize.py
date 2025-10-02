"""Text anonymization utilities."""

import re


def anonymize_chat_context(text: str, user_id: int) -> str:
    """
    Anonymize chat context by removing PII.

    Args:
        text: Chat context to anonymize
        user_id: User ID to replace

    Returns:
        Anonymized text
    """
    anonymized = text

    # Replace user IDs
    anonymized = anonymized.replace(str(user_id), "[USER]")

    # Remove phone numbers (Russian format)
    anonymized = re.sub(r"\+?7[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}", "[PHONE]", anonymized)
    anonymized = re.sub(r"\+?[0-9]{10,15}", "[PHONE]", anonymized)

    # Remove email addresses
    anonymized = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", anonymized)

    # Remove URLs
    anonymized = re.sub(r"https?://\S+", "[URL]", anonymized)

    # TODO: Add more sophisticated PII removal:
    # - Named Entity Recognition for person names
    # - Location data
    # - Passport/ID numbers
    # - Credit card numbers

    return anonymized
