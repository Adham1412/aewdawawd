"""Telegram bot: opens the Mini App, lists orders and receives payment receipts.

The bot NEVER asks for Telegram passwords, login codes or SMS codes.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal, init_dev_schema
from app.models.entities import Order, Product, User
from app.services import order_states as st
from app.services.orders import transition_order

log = logging.getLogger("starmarket.bot")
router = Router()
SAFETY = "Eslatma: bot sizdan hech qachon Telegram paroli yoki SMS-kod so'ramaydi."


def _buttons(is_admin: bool) -> InlineKeyboardMarkup | None:
    rows = []
    if settings.miniapp_url.startswith("https://"):
        rows.append([InlineKeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=settings.miniapp_url))])
    if is_admin and settings.admin_url.startswith("https://"):
        rows.append([InlineKeyboardButton(text="🛠 Admin panel", web_app=WebAppInfo(url=settings.admin_url))])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


@router.message(CommandStart())
async def start(message: Message):
    is_admin = message.from_user.id in settings.admin_ids
    kb = _buttons(is_admin)
    text = ("Assalomu alaykum! StarMarket: Telegram Stars va Premium.\n\n"
            "1) Do'kon tugmasi orqali mahsulotni tanlang va buyurtma bering.\n"
            "2) Ko'rsatilgan rekvizitga to'lang.\n"
            "3) To'lov chekining rasmini shu chatga yuboring.\n\n" + SAFETY)
    if kb is None:
        text += "\n\n(Mini App manzili hali sozlanmagan: MINIAPP_URL.)"
    await message.answer(text, reply_markup=kb)


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("/start — do'kon\n/orders — buyurtmalarim\nTo'lov chekini rasm qilib yuboring.\n\n" + SAFETY)


@router.message(Command("orders"))
async def orders_command(message: Message):
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(Order, Product).join(User, Order.user_id == User.id).join(Product, Order.product_id == Product.id)
            .where(User.telegram_id == message.from_user.id).order_by(Order.created_at.desc()).limit(10))).all()
    if not rows:
        await message.answer("Hozircha buyurtma yo'q. /start bosing.")
        return
    await message.answer("\n".join(f"#{o.id[:8]} · {p.name_uz} ×{o.quantity} · {st.STATUS_TEXT_UZ.get(o.status, o.status)}" for o, p in rows))


@router.message(F.photo)
async def receipt(message: Message, bot: Bot):
    async with SessionLocal() as db:
        found = (await db.execute(
            select(Order, Product, User).join(User, Order.user_id == User.id).join(Product, Order.product_id == Product.id)
            .where(User.telegram_id == message.from_user.id, Order.status == st.AWAITING_PAYMENT)
            .order_by(Order.created_at.desc()).limit(1).with_for_update(of=Order))).first()
        if found is None:
            await message.answer("To'lov kutayotgan buyurtma topilmadi. Avval do'konda buyurtma bering: /start")
            return
        order, product, user = found
        try:
            await transition_order(db, order, st.PAYMENT_SUBMITTED, message.from_user.id, "receipt received")
        except st.InvalidTransition:
            await message.answer("Buyurtma holati o'zgargan. /orders ni tekshiring.")
            return
        caption = (f"💳 Chek: buyurtma #{order.id[:8]}\n{product.name_uz} ×{order.quantity}\n"
                   f"Summa: {order.total_amount} {order.currency}\n"
                   f"Mijoz: {user.telegram_id} @{user.username or '-'}\nQabul qiluvchi: {order.customer_details_json}\n"
                   f"Pul kartaga tushganini bank ilovasida tekshirib, admin panelda tasdiqlang.")
    await message.answer(f"Chek qabul qilindi (buyurtma #{order.id[:8]}). Admin tekshirgach xabar beramiz.")
    for admin_id in settings.admin_ids:
        try:
            await bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption,
                                 reply_markup=_buttons(True))
        except Exception as exc:
            log.warning("could not notify admin %s: %s", admin_id, type(exc).__name__)


@router.message()
async def fallback(message: Message):
    await message.answer("Tushunmadim. /start yoki /orders ni bosing, to'lov chekini rasm qilib yuboring.\n" + SAFETY)


async def main():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Set it in .env before starting the bot.")
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings.validate_production_secrets()
    await init_dev_schema()
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
