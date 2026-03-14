"""
Magic link token service for survey invitations.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


class TokenService:
    """Manages magic link tokens for survey invitations."""

    def generate_token(self) -> uuid.UUID:
        """Generate a cryptographically secure UUID token."""
        return uuid.uuid4()

    def get_expiry_date(self, hours: int = None) -> object:
        """Calculate token expiry date. Default: 48 hours (per architecture requirement)."""
        hours = hours or getattr(settings, 'SURVEY_TOKEN_EXPIRY_HOURS', 48)
        return timezone.now() + timedelta(hours=hours)

    def is_expired(self, expires_at) -> bool:
        """Check if a token has expired."""
        return timezone.now() > expires_at


token_service = TokenService()
