import hashlib
import hmac
import json
import os
import tempfile
import time
from urllib.parse import urlencode

# Must be set before `app` is imported anywhere.
_DB = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.update({
    "APP_ENV": "development",
    "DATABASE_URL": f"sqlite+aiosqlite:///{_DB}",
    "BOT_TOKEN": "123456:TEST-TOKEN",
    "SESSION_SECRET": "test-secret-that-is-long-enough-for-tests-123456",
    "ADMIN_TELEGRAM_IDS": "999",
    "PAYMENT_INSTRUCTIONS": "Karta: 0000 (test)",
})


def make_init_data(user: dict, bot_token: str = "123456:TEST-TOKEN") -> str:
    values = {"auth_date": str(int(time.time())), "user": json.dumps(user, separators=(",", ":"))}
    check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)
