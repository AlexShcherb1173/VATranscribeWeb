from __future__ import annotations

import hashlib
import secrets


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_refresh_token_hash(token: str, token_hash: str) -> bool:
    return hash_refresh_token(token) == token_hash
