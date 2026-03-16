"""
AES-256-GCM encryption service for PII fields.
HMAC-SHA256 for irreversible display hashes (LGPD compliance).
"""
import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class CryptoService:
    """
    AES-256-GCM encryption for PII data (email, name).
    Nonce is prepended to ciphertext and base64-encoded.
    """

    def __init__(self):
        key_b64 = settings.ENCRYPTION_KEY
        if not key_b64:
            raise ValueError(
                'ENCRYPTION_KEY não configurada. '
                'Gere com: python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"'
            )
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError(
                'ENCRYPTION_KEY deve ser base64 de exatamente 32 bytes (256 bits). '
                'Gere com: python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"'
            )
        self.aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string using AES-256-GCM. Returns base64(nonce + ciphertext)."""
        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt(self, encrypted: str) -> str:
        """Decrypt a base64(nonce + ciphertext) string."""
        data = base64.b64decode(encrypted)
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')

    def encrypt_if_needed(self, value: str) -> str:
        """Encrypt only if not already encrypted (for idempotent saves)."""
        try:
            # Try decrypting - if it works, it's already encrypted
            self.decrypt(value)
            return value
        except Exception:
            return self.encrypt(value)

    def compute_email_hash(self, email: str) -> str:
        """
        Compute a deterministic, irreversible HMAC-SHA256 hash of an email address.

        Used for LGPD-compliant display on the frontend — the actual email is never
        exposed via API. The hash is consistent (same email → same hash) and cannot
        be reversed without the secret key.

        Returns: first 16 hex characters of HMAC-SHA256(SECRET_KEY, email.lower())
        """
        secret = getattr(settings, 'EMAIL_HASH_SECRET', settings.SECRET_KEY)
        digest = hmac.new(
            secret.encode('utf-8'),
            email.lower().strip().encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return digest[:16]


try:
    crypto_service = CryptoService()
except ValueError:
    # Allow import without crashing during migrations/docs generation
    crypto_service = None  # type: ignore
