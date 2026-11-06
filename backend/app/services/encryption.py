import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

class DataEncryptionService:
    """
    Transparent at-rest field encryption using AES-128 via Fernet.
    Activated when FINSIGHT_ENCRYPTION_KEY environment variable is configured.
    """

    @classmethod
    def get_key(cls) -> Optional[bytes]:
        env_key = os.environ.get("FINSIGHT_ENCRYPTION_KEY")
        if env_key:
            return env_key.strip().encode("utf-8") if isinstance(env_key, str) else env_key
        return None

    @classmethod
    def is_enabled(cls) -> bool:
        key = cls.get_key()
        if not key:
            return False
        try:
            Fernet(key)
            return True
        except Exception:
            return False

    @classmethod
    def generate_key(cls) -> str:
        """Generates a valid 32-byte URL-safe base64-encoded Fernet key."""
        return Fernet.generate_key().decode("utf-8")

    @classmethod
    def encrypt(cls, text: Optional[str]) -> str:
        if not text:
            return ""
        if not cls.is_enabled():
            return str(text)
        try:
            f = Fernet(cls.get_key())
            encrypted = f.encrypt(str(text).encode("utf-8")).decode("utf-8")
            return f"enc:{encrypted}"
        except Exception:
            return str(text)

    @classmethod
    def decrypt(cls, text: Optional[str]) -> str:
        if not text:
            return ""
        str_val = str(text)
        if not str_val.startswith("enc:"):
            return str_val
        if not cls.is_enabled():
            return str_val
        try:
            token = str_val[4:].encode("utf-8")
            f = Fernet(cls.get_key())
            return f.decrypt(token).decode("utf-8")
        except (InvalidToken, Exception):
            return str_val
