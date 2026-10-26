import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.ratelimit import auth_limiter
from app.core.security import create_session_token, verify_telegram_init_data
from app.db.session import get_db
from app.models.entities import User
from app.schemas.api import AuthResponse, AuthUser, TelegramAuthRequest

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/telegram", response_model=AuthResponse, summary="Verify Telegram Mini App initData")
async def telegram_auth(request: Request, body: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    auth_limiter.hit(f"auth:{request.client.host if request.client else 'unknown'}")
    if not settings.bot_token:
        raise HTTPException(status_code=503, detail="Telegram authentication is not configured")
    try:
        verified = verify_telegram_init_data(body.init_data, settings.bot_token, settings.telegram_initdata_max_age_seconds)
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Telegram authentication could not be verified")
    tg_user = verified["user"]
    result = await db.execute(select(User).where(User.telegram_id == tg_user["id"]))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=tg_user["id"], username=tg_user.get("username"),
                    first_name=tg_user.get("first_name"),
                    language=(tg_user.get("language_code") or "uz")[:5])
        db.add(user)
    else:
        user.username = tg_user.get("username")
        user.first_name = tg_user.get("first_name")
        if tg_user.get("language_code"):
            user.language = tg_user["language_code"][:5]
    try:
        await db.commit()
    except IntegrityError:  # two parallel first logins of the same user
        await db.rollback()
        user = (await db.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one()
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_session_token(user.telegram_id)
    return AuthResponse(
        access_token=token, expires_in=settings.session_ttl_seconds,
        user=AuthUser(id=user.telegram_id, first_name=user.first_name, username=user.username,
                      language_code=user.language, is_admin=user.telegram_id in settings.admin_ids),
    )
