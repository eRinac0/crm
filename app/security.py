"""Password hashing and short-lived signed bearer tokens."""

import base64
import hashlib
import hmac
import json
import os
import time

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()
ACCESS_TOKEN_TTL_SECONDS = 30 * 60


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(password, hashed_password)
    except (ValueError, TypeError):
        return False


# Used to keep unknown-email login attempts at roughly the same hash cost.
DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password-000000")


def _secret_key() -> bytes:
    key = os.getenv("CRM_SECRET_KEY", "").encode("utf-8")
    if len(key) < 32:
        raise RuntimeError("CRM_SECRET_KEY must contain at least 32 bytes")
    return key


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    payload = json.dumps(
        {"sub": str(user_id), "iat": now, "exp": now + ACCESS_TOKEN_TTL_SECONDS},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded = _b64encode(payload)
    signature = hmac.new(_secret_key(), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded}.{_b64encode(signature)}"


def verify_access_token(token: str) -> int | None:
    try:
        encoded, supplied_signature = token.split(".", maxsplit=1)
        expected_signature = _b64encode(
            hmac.new(_secret_key(), encoded.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None

        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        user_id = int(payload["sub"])
        issued_at = int(payload["iat"])
        expires_at = int(payload["exp"])
        now = int(time.time())
        if user_id <= 0 or issued_at > now or expires_at <= now:
            return None
        if expires_at - issued_at > ACCESS_TOKEN_TTL_SECONDS:
            return None
        return user_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError, RuntimeError):
        return None


def verify_registration_key(supplied_key: str) -> bool:
    configured_key = os.getenv("CRM_REGISTRATION_KEY", "")
    return bool(configured_key) and hmac.compare_digest(supplied_key, configured_key)
