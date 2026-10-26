"""Best-effort Telegram notifications. Never raises; never logs the bot token."""
import logging

import httpx

from app.core.config import settings

log = logging.getLogger("starmarket.notify")
# httpx logs full request URLs at INFO and the Bot API URL contains the token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


async def send_telegram_message(chat_id: int, text: str) -> bool:
    if not settings.bot_token:
        return False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000]},
            )
        if resp.status_code != 200:
            log.warning("sendMessage failed status=%s chat=%s", resp.status_code, chat_id)
            return False
        return True
    except Exception as exc:  # network errors must not break order processing
        log.warning("sendMessage error type=%s chat=%s", type(exc).__name__, chat_id)
        return False
