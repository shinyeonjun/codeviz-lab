from __future__ import annotations

import hashlib
import secrets


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200_000,
    )
    return f"{salt}${derived.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt, digest = hashed_password.split("$", maxsplit=1)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200_000,
    )
    return secrets.compare_digest(digest, derived.hex())
