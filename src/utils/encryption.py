"""
Утилиты для шифрования/дешифрования API ключей.

Использует симметричное шифрование Fernet (AES-128 в режиме CBC).
"""

import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from ..config.settings import settings


logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """
    Получить экземпляр Fernet для шифрования/дешифрования.

    Использует ENCRYPTION_KEY из настроек для создания ключа шифрования.
    """
    # Используем PBKDF2 для создания ключа из пароля
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'ozon_fbo_bot_salt',  # В production использовать уникальную соль
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(
        kdf.derive(settings.encryption_key.encode())
    )

    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """
    Зашифровать API ключ.

    Args:
        api_key: Незашифрованный API ключ

    Returns:
        str: Зашифрованный API ключ в виде строки

    Example:
        >>> encrypted = encrypt_api_key("my-secret-key")
        >>> print(encrypted)
        'gAAAAABh...'
    """
    try:
        fernet = _get_fernet()
        encrypted_bytes = fernet.encrypt(api_key.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Error encrypting API key: {str(e)}")
        raise


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Расшифровать API ключ.

    Args:
        encrypted_key: Зашифрованный API ключ

    Returns:
        str: Расшифрованный API ключ

    Raises:
        ValueError: Если не удалось расшифровать ключ

    Example:
        >>> decrypted = decrypt_api_key("gAAAAABh...")
        >>> print(decrypted)
        'my-secret-key'
    """
    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted_key.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Error decrypting API key: {str(e)}")
        raise ValueError("Не удалось расшифровать API ключ")
