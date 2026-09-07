from cryptography.fernet import Fernet

from social_agent.config import get_settings


def _get_fernet() -> Fernet:
    key = get_settings().token_encryption_key.get_secret_value()
    return Fernet(key.encode())


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()