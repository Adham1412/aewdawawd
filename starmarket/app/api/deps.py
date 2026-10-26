from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.core.ratelimit import admin_limiter
from app.core.security import verify_session_token


async def current_telegram_id(authorization: str | None = Header(default=None)) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    return verify_session_token(authorization.split(" ", 1)[1].strip())


async def current_admin(telegram_id: int = Depends(current_telegram_id)) -> int:
    """Admin = Telegram ID listed in ADMIN_TELEGRAM_IDS (checked on every request)."""
    if telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Administrator access required")
    admin_limiter.hit(f"admin:{telegram_id}")
    return telegram_id
