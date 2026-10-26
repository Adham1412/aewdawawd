import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
import pytest
from app.core.security import verify_telegram_init_data


def build_init_data(bot_token: str, user: dict, auth_date: int | None = None) -> str:
    values = {"auth_date": str(auth_date or int(time.time())), "user": json.dumps(user, separators=(",", ":"))}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


def test_verify_valid_telegram_initdata():
    raw = build_init_data("test-bot-token", {"id": 12345, "first_name": "Test"})
    result = verify_telegram_init_data(raw, "test-bot-token")
    assert result["user"]["id"] == 12345


def test_reject_tampered_initdata():
    raw = build_init_data("test-bot-token", {"id": 12345, "first_name": "Test"}) + "&username=forged"
    with pytest.raises(ValueError):
        verify_telegram_init_data(raw, "test-bot-token")


def test_reject_expired_initdata():
    raw = build_init_data("test-bot-token", {"id": 12345}, auth_date=int(time.time()) - 99999)
    with pytest.raises(ValueError):
        verify_telegram_init_data(raw, "test-bot-token", max_age_seconds=60)


def test_session_token_expiry_and_signature(monkeypatch):
    from app.core import security
    monkeypatch.setattr(security.settings, "session_secret", "test-secret-that-is-long-enough-for-tests-123")
    token = security.create_session_token(987654, ttl_seconds=60)
    assert security.verify_session_token(token) == 987654
    bad = token[:-1] + ("A" if token[-1] != "A" else "B")
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        security.verify_session_token(bad)
