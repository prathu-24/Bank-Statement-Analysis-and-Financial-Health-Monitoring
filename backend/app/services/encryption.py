import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

class DataEncryptionService:
    """
    Transparent at-rest field encryption using AES-128 via Fernet.
    Activated when FINSIGHT_ENCRYPTION_KEY environment variable is configured.
    When unset, statements are stored UNENCRYPTED in SQLite.
    When configured, bad keys or corrupted tokens fail loudly (no silent fallback).
    """

    @classmethod
    def get_key(cls) -> Optional[bytes]:
        env_key = os.environ.get("FINSIGHT_ENCRYPTION_KEY")
        if env_key:
            trimmed = env_key.strip()
            if trimmed:
                return trimmed.encode("utf-8") if isinstance(trimmed, str) else trimmed
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
        """
        Encrypts text using Fernet.
        If key is unset, returns plain text (unencrypted storage).
        If key is configured but invalid, fails loudly with ValueError.
        """
        if not text:
            return ""
        key = cls.get_key()
        if not key:
            return str(text)

        try:
            f = Fernet(key)
            encrypted = f.encrypt(str(text).encode("utf-8")).decode("utf-8")
            return f"enc:{encrypted}"
        except Exception as e:
            raise ValueError(f"Encryption failed with configured FINSIGHT_ENCRYPTION_KEY: {str(e)}")

    @classmethod
    def decrypt(cls, text: Optional[str]) -> str:
        """
        Decrypts text with 'enc:' prefix using Fernet.
        If text is unencrypted plaintext, returns it as-is.
        If text has 'enc:' prefix but key is unset or decryption fails, fails loudly with ValueError.
        """
        if not text:
            return ""
        str_val = str(text)
        if not str_val.startswith("enc:"):
            return str_val

        key = cls.get_key()
        if not key:
            raise ValueError(
                "Decryption failed: Field was encrypted with 'enc:' prefix, but FINSIGHT_ENCRYPTION_KEY is unset."
            )

        try:
            token = str_val[4:].encode("utf-8")
            f = Fernet(key)
            return f.decrypt(token).decode("utf-8")
        except InvalidToken:
            raise ValueError(
                "Decryption failed: Token is invalid, corrupted, or was encrypted with a different key. Silent fallback is prohibited."
            )
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}. Silent fallback is prohibited.")
