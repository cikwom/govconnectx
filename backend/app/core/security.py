import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import load_dotenv  # noqa: F401 - ensure .env is loaded before reading settings

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    if ENVIRONMENT == "production":
        raise RuntimeError("JWT_SECRET must be configured in production")
    JWT_SECRET = "development-only-change-this-secret-before-deploying"
if ENVIRONMENT == "production" and len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET must contain at least 32 characters in production")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
PASSWORD_ITERATIONS = 600_000
MIN_PASSWORD_ITERATIONS = 100_000
MAX_PASSWORD_ITERATIONS = 1_000_000
PASSWORD_SALT_BYTES = 16
PASSWORD_DIGEST_BYTES = 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256$" + str(PASSWORD_ITERATIONS) + "$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a stored PBKDF2 hash without allowing attacker-controlled work factors."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    try:
        algorithm, iterations_text, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)
        if not MIN_PASSWORD_ITERATIONS <= iterations <= MAX_PASSWORD_ITERATIONS:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
        if len(salt) != PASSWORD_SALT_BYTES or len(expected_digest) != PASSWORD_DIGEST_BYTES:
            return False

        calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(calculated, expected_digest)
    except (ValueError, TypeError, OverflowError):
        return False


def create_access_token(user_id: int, role: str, token_version: int = 0) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "ver": token_version,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
