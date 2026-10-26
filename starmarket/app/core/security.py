"""Telegram Mini App verification and short-lived signed sessions."""
import hashlib
import hmac
import json
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from urllib.parse import parse_qsl

from fastapi import HTTPException, status

from app.core.config import settings


def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict:
    """Verify Telegram WebApp initData per Telegram's HMAC procedure.

    Never trust user fields from the browser until this check succeeds.
    """
    if not init_data or not bot_token:
        raise ValueError("initData and bot token are required")
    parsed = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("initData hash is missing")
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise ValueError("Invalid initData signature")
    auth_date = int(parsed.get("auth_date", "0"))
    now = int(time.time())
    if auth_date <= 0 or auth_date > now + 60 or now - auth_date > max_age_seconds:
        raise ValueError("initData is expired or auth_date is invalid")
    user_json = parsed.get("user")
    if not user_json:
        raise ValueError("Telegram user is missing")
    user = json.loads(user_json)
    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise ValueError("Telegram user ID is invalid")
    return {"user": user, "auth_date": auth_date, "query_id": parsed.get("query_id")}


def _b64(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_session_token(user_id: int, ttl_seconds: int | None = None) -> str:
    if len(settings.session_secret) < 32:
        raise RuntimeError("SESSION_SECRET must be set to a random secret of at least 32 characters")
    ttl = ttl_seconds or settings.session_ttl_seconds
    payload = _b64(json.dumps({"sub": user_id, "exp": int(time.time()) + ttl}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def verify_session_token(token: str) -> int:
    try:
        payload, signature = token.split(".", 1)
        expected = _b64(hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature):
            raise ValueError("bad signature")
        data = json.loads(_unb64(payload))
        if int(data["exp"]) < int(time.time()):
            raise ValueError("expired")
        return int(data["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session") from exc
