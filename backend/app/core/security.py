"""Security utilities for student authentication, PIN hashing, and JWT tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.core.config import get_settings


def _b64encode_url(data: bytes) -> str:
    """Base64url encode without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode_url(encoded: str) -> bytes:
    """Base64url decode with padding restored."""
    rem = len(encoded) % 4
    if rem:
        encoded += "=" * (4 - rem)
    return base64.urlsafe_b64decode(encoded.encode("utf-8"))


def hash_pin(pin: str) -> str:
    """Hash a numeric student PIN with PBKDF2-HMAC-SHA256 and a cryptographically secure random salt."""
    if not pin or len(pin) < 4:
        raise ValueError("PIN must be at least 4 digits")
    salt = secrets.token_bytes(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}${salt.hex()}${derived.hex()}"


def verify_pin(pin: str, stored_hash: str) -> bool:
    """Verify a student PIN against a stored PBKDF2 hash using constant-time comparison."""
    if not stored_hash or "$" not in stored_hash:
        return False
    try:
        header, salt_hex, hash_hex = stored_hash.split("$")
        parts = header.split(":")
        if len(parts) != 3 or parts[0] != "pbkdf2" or parts[1] != "sha256":
            return False
        iterations = int(parts[2])
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        computed = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iterations)
        return secrets.compare_digest(computed, expected)
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta_seconds: int = 30 * 86400,
) -> str:
    """Create an RFC 7519 compliant JSON Web Token (HS256) signed with application secret key."""
    settings = get_settings()
    secret_key = settings.secret_key.encode("utf-8")

    now = int(time.time())
    payload = dict(data)
    payload["iat"] = now
    payload["exp"] = now + expires_delta_seconds

    header_bytes = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    encoded_header = _b64encode_url(header_bytes)
    encoded_payload = _b64encode_url(payload_bytes)

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
    encoded_sig = _b64encode_url(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_sig}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Validate and decode a JSON Web Token, returning payload dict or None if invalid/expired."""
    if not token or token.count(".") != 2:
        return None
    try:
        settings = get_settings()
        secret_key = settings.secret_key.encode("utf-8")

        encoded_header, encoded_payload, encoded_sig = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_sig = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
        provided_sig = _b64decode_url(encoded_sig)

        if not secrets.compare_digest(expected_sig, provided_sig):
            return None

        payload_bytes = _b64decode_url(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if exp and int(time.time()) > exp:
            return None

        return payload
    except Exception:
        return None
