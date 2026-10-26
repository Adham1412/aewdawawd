import json
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_telegram_id
from app.core.ratelimit import order_limiter
from app.db.session import get_db
from app.models.entities import Order, Product, User
from app.schemas.api import OrderCreate, OrderOut
from app.services import order_states as st
from app.services.orders import transition_order

router = APIRouter(prefix="/orders", tags=["orders"])
MAX_OPEN_ORDERS_PER_USER = 5


def order_out(o: Order, message: str = "") -> OrderOut:
    return OrderOut(id=o.id, product_id=o.product_id, quantity=o.quantity, total_amount=o.total_amount,
                    currency=o.currency, status=o.status, created_at=o.created_at, message=message,
                    status_text=st.STATUS_TEXT_UZ.get(o.status, o.status))


async def _active_user(db: AsyncSession, telegram_id: int) -> User:
    user = (await db.execute(select(User).where(User.telegram_id == telegram_id, User.is_active.is_(True)))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User profile not found; authenticate again")
    return user


@router.post("", response_model=OrderOut, status_code=201, summary="Create an unpaid order")
async def create_order(body: OrderCreate, telegram_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    order_limiter.hit(f"order:{telegram_id}")
    user = await _active_user(db, telegram_id)
    old = (await db.execute(select(Order).where(Order.idempotency_key == body.idempotency_key))).scalar_one_or_none()
    if old is not None:
        if old.user_id != user.id:
            raise HTTPException(status_code=409, detail="Idempotency key already used")
        return order_out(old, "Existing order returned; no duplicate created")
    open_count = (await db.execute(select(func.count()).select_from(Order).where(
        Order.user_id == user.id, Order.status.in_(st.OPEN_STATUSES)))).scalar_one()
    if open_count >= MAX_OPEN_ORDERS_PER_USER:
        raise HTTPException(status_code=409, detail="Too many open orders. Finish or cancel one first.")
    product = (await db.execute(select(Product).where(Product.id == body.product_id, Product.is_active.is_(True)))).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product is not available")
    if product.category not in {"stars", "premium"} or product.amount <= 0:
        raise HTTPException(status_code=400, detail="This product is not enabled for sale")
    if product.category == "premium" and body.quantity != 1:
        raise HTTPException(status_code=400, detail="Premium can be ordered one at a time")
    # Server-calculated amount only; never trust a price sent by the browser.
    total = Decimal(product.price) * body.quantity
    order = Order(user_id=user.id, product_id=product.id, quantity=body.quantity, total_amount=total,
                  currency=product.currency, status=st.AWAITING_PAYMENT,
                  customer_details_json=json.dumps(body.customer_details), idempotency_key=body.idempotency_key)
    db.add(order)
    try:
        await db.commit()
    except IntegrityError:  # parallel duplicate request with the same key
        await db.rollback()
        old = (await db.execute(select(Order).where(Order.idempotency_key == body.idempotency_key))).scalar_one_or_none()
        if old is None or old.user_id != user.id:
            raise HTTPException(status_code=409, detail="Could not create order safely; retry with a new key")
        return order_out(old, "Existing order returned; no duplicate created")
    return order_out(order, "Order created. Pay using the instructions, then send the receipt to the bot.")


@router.get("", response_model=list[OrderOut], summary="My latest orders")
async def my_orders(telegram_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Order).join(User, Order.user_id == User.id).where(User.telegram_id == telegram_id)
                            .order_by(Order.created_at.desc()).limit(20))
    return [order_out(o) for o in rows.scalars().all()]


async def _own_order(db: AsyncSession, order_id: str, telegram_id: int, lock: bool = False) -> Order:
    q = select(Order).join(User, Order.user_id == User.id).where(Order.id == order_id, User.telegram_id == telegram_id)
    if lock:
        q = q.with_for_update(of=Order)
    order = (await db.execute(q)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/{order_id}", response_model=OrderOut, summary="Get own order status")
async def get_order(order_id: str, telegram_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    return order_out(await _own_order(db, order_id, telegram_id))


@router.post("/{order_id}/cancel", response_model=OrderOut, summary="Cancel own unpaid order")
async def cancel_order(order_id: str, telegram_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    order = await _own_order(db, order_id, telegram_id, lock=True)
    if order.status != st.AWAITING_PAYMENT:
        raise HTTPException(status_code=409, detail="Only unpaid orders can be cancelled by the customer")
    try:
        await transition_order(db, order, st.CANCELLED, telegram_id, "cancelled by customer")
    except st.InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return order_out(order, "Order cancelled")
