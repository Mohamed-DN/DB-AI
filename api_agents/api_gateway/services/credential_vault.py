"""
Credential Encryption Service for M-DN DBA AI
AES-256-GCM encryption for database credentials stored in MongoDB.

This provides:
- Secure at-rest encryption for passwords
- Environment-based master key management
- Transparent encrypt/decrypt helpers
"""
import os
import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional


class CredentialVault:
    """
    Secure credential encryption/decryption using AES-256-GCM.
    
    Usage:
        vault = CredentialVault()
        encrypted = vault.encrypt("my_password")
        decrypted = vault.decrypt(encrypted)
    """
    
    # Environment variable for master key
    MASTER_KEY_ENV = "M-DN_MASTER_KEY"
    
    # Salt for key derivation (should be consistent)
    SALT_ENV = "M-DN_ENCRYPTION_SALT"
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize vault with master key.
        
        Args:
            master_key: Optional master key. If not provided, reads from
                       M-DN_MASTER_KEY environment variable.
        """
        self._master_key = master_key or os.getenv(self.MASTER_KEY_ENV)
        
        if not self._master_key:
            # Generate a default key for development (NOT for production!)
            self._master_key = "m-dn-dev-master-key-change-in-production"
            print("⚠️  WARNING: Using default master key. Set M-DN_MASTER_KEY for production!")
        
        # Get or generate salt
        salt_b64 = os.getenv(self.SALT_ENV)
        if salt_b64:
            self._salt = base64.b64decode(salt_b64)
        else:
            # Use a consistent salt for development
            self._salt = b"m-dn_salt_dev_16"  # 16 bytes
        
        # Derive encryption key using PBKDF2
        self._encryption_key = self._derive_key(self._master_key, self._salt)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a 256-bit key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        return kdf.derive(password.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Returns:
            Base64-encoded string containing: nonce (12 bytes) + ciphertext + tag
        """
        if not plaintext:
            return ""
        
        # Generate random nonce (12 bytes for GCM)
        nonce = secrets.token_bytes(12)
        
        # Encrypt using AES-256-GCM
        aesgcm = AESGCM(self._encryption_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Combine nonce + ciphertext and encode to base64
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_b64: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted_b64: Base64-encoded encrypted data (nonce + ciphertext + tag)
        
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_b64:
            return ""
        
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_b64)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            # Decrypt using AES-256-GCM
            aesgcm = AESGCM(self._encryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode()
        
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def rotate_key(self, old_encrypted: str, new_vault: 'CredentialVault') -> str:
        """
        Rotate encryption key by re-encrypting with new key.
        
        Args:
            old_encrypted: Data encrypted with current key
            new_vault: CredentialVault instance with new key
        
        Returns:
            Data re-encrypted with new key
        """
        plaintext = self.decrypt(old_encrypted)
        return new_vault.encrypt(plaintext)
    
    @staticmethod
    def generate_master_key() -> str:
        """Generate a cryptographically secure master key"""
        return base64.b64encode(secrets.token_bytes(32)).decode()
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt (base64 encoded)"""
        return base64.b64encode(secrets.token_bytes(16)).decode()


# =============================================================================
# Helper Functions for MongoDB Credential Fields
# =============================================================================

# Global vault instance
_vault: Optional[CredentialVault] = None


def get_vault() -> CredentialVault:
    """Get singleton vault instance"""
    global _vault
    if _vault is None:
        _vault = CredentialVault()
    return _vault


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential for storage"""
    return get_vault().encrypt(plaintext)


def decrypt_credential(encrypted: str) -> str:
    """Decrypt a stored credential"""
    return get_vault().decrypt(encrypted)


def encrypt_db_credentials(credentials: dict) -> dict:
    """
    Encrypt sensitive fields in a credentials dictionary.
    
    Args:
        credentials: Dict with 'password', 'admin_password', etc.
    
    Returns:
        Dict with encrypted versions of sensitive fields
    """
    vault = get_vault()
    encrypted = {}
    
    # Fields to encrypt
    sensitive_fields = ['password', 'admin_password', 'app_password', 'secret_key']
    
    for key, value in credentials.items():
        if key in sensitive_fields and value:
            encrypted[f"{key}_encrypted"] = vault.encrypt(value)
        else:
            encrypted[key] = value
    
    return encrypted


def decrypt_db_credentials(credentials: dict) -> dict:
    """
    Decrypt sensitive fields in a credentials dictionary.
    
    Args:
        credentials: Dict with '*_encrypted' fields
    
    Returns:
        Dict with decrypted versions (original field names)
    """
    vault = get_vault()
    decrypted = {}
    
    for key, value in credentials.items():
        if key.endswith('_encrypted') and value:
            original_key = key.replace('_encrypted', '')
            decrypted[original_key] = vault.decrypt(value)
        else:
            decrypted[key] = value
    
    return decrypted


# =============================================================================
# CLI for key generation
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        print("🔐 M-DN DBA AI - Credential Vault Key Generator")
        print("=" * 50)
        print(f"M-DN_MASTER_KEY={CredentialVault.generate_master_key()}")
        print(f"M-DN_ENCRYPTION_SALT={CredentialVault.generate_salt()}")
        print("=" * 50)
        print("Add these to your .env file for production!")
    else:
        # Demo
        vault = CredentialVault()
        
        print("🔐 Credential Vault Demo")
        print("=" * 50)
        
        original = "SuperSecretPassword123!"
        encrypted = vault.encrypt(original)
        decrypted = vault.decrypt(encrypted)
        
        print(f"Original:  {original}")
        print(f"Encrypted: {encrypted}")
        print(f"Decrypted: {decrypted}")
        print(f"Match:     {original == decrypted}")
        
        print("\n📋 To generate production keys, run:")
        print("   python credential_vault.py generate")
