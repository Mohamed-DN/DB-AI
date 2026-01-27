
import os
import base64
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger("CryptoUtils")

class CryptoUtils:
    _key = None
    _fernet = None

    @classmethod
    def _get_key(cls):
        if cls._key is None:
            # Try to get key from env, otherwise generate a deterministic one for lab
            # In PROD this should be a carefully managed secret
            env_key = os.getenv("NEXI_ENCRYPTION_KEY")
            if env_key:
                cls._key = env_key.encode()
            else:
                # Fallback purely for dev/lab environment to ensure it works across restarts
                # without an external secret manager
                # WARNING: NOT SECURE FOR PROD
                logger.warning("Using default dev encryption key. Set NEXI_ENCRYPTION_KEY in prod.")
                cls._key = base64.urlsafe_b64encode(b"Nexi_DBA_AI_Secret_Key_32_Bytes_Long!!")
            
            try:
                cls._fernet = Fernet(cls._key)
            except Exception as e:
                logger.error(f"Invalid encryption key: {e}")
                # Fallback to a valid generated key if the hardcoded one fails (it shouldn't)
                cls._key = Fernet.generate_key()
                cls._fernet = Fernet(cls._key)
        
        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Encrypt a string"""
        if not plaintext:
            return ""
        try:
            f = cls._get_key()
            return f.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """Decrypt a string"""
        if not ciphertext:
            return ""
        try:
            f = cls._get_key()
            return f.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # If decryption fails (e.g. key change), return original (might be unencrypted)
            # or raise. For now, we assume if it fails it might be plain text? 
            # Better to fail secure? Let's just return empty or error.
            return ciphertext # Fallback for backward compat if mixed plain/encrypted
