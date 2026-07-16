"""Fernet encryption for sensitive stored values (AI API keys)."""

from cryptography.fernet import Fernet
from pathlib import Path


KEY_FILE = "./data/.viberails_key"


def _get_or_create_key() -> bytes:
    """Load the Fernet key from file, or generate and persist a new one."""
    key_path = Path(KEY_FILE)
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    return key


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value."""
    f = Fernet(_get_or_create_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    f = Fernet(_get_or_create_key())
    return f.decrypt(ciphertext.encode()).decode()
