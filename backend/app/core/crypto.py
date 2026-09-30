from __future__ import annotations
import json

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().master_key.encode()
    return Fernet(key)


def encrypt_credentials(data: dict | None) -> bytes | None:
    if not data:
        return None
    return _fernet().encrypt(json.dumps(data).encode())


def decrypt_credentials(blob: bytes | None) -> dict | None:
    if not blob:
        return None
    try:
        return json.loads(_fernet().decrypt(blob).decode())
    except InvalidToken:
        return None
