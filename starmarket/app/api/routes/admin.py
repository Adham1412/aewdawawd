import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_admin
from app.db.session import get_db
from app.models.entities import AuditLog, LedgerEntry, Order, Product, User
from app.schemas.api import (AdminOrderOut, AdminProductOut, ProductIn, ProductPatch,
                             TransitionRequest)
from app.services import order_states as st
from app.services.notify import send_telegram_message
from app.services.orders import transition_order

log = logging.getLogger("starmarket.admin")
router = APIRouter(prefix="/admin", tags=["admin"])

CUSTOMER_MESSAGES = {
    st.PAID: "To'lovingiz tasdiqlandi. Buyurtma tez orada bajariladi.",
    st.PROCESSING: "Buyurtmangiz bajarilmoqda.",
    st.COMPLETED: "Buyurtmangiz bajarildi. Rahmat!",
    st.FAILED: "Buyurtmani bajarishda muammo chiqdi. Admin siz bilan bog'lanadi.",
    st.CANCELLED: "Buyurtma bekor qilindi.",
    st.REFUND_PENDING: "Pulingizni qaytarish jarayoni boshlandi.",
    st.REFUNDED: "Pulingiz qaytarildi.",
    st.AWAITING_PAYMENT: "Chek tasdiqlanmadi. Iltimos, to'lovni tekshirib, aniq chekni qayta yuboring.",
}


def _details(o: Order) -> dict[str, str]:
    try:
        d = json.loads(o.customer_details_json or "{}")
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except ValueError:
        return {}


def _admin_order(o: Order, u: User, p: Product) -> AdminOrderOut:
    return AdminOrderOut(
        id=o.id, product_id=o.product_id, quantity=o.quantity, total_amount=o.total_amount,
        currency=o.currency, status=o.status, created_at=o.created_at,
        status_text=st.STATUS_TEXT_UZ.get(o.status, o.status), product_name=p.name_uz,
        customer_telegram_id=u.telegram_id, customer_username=u.username, customer_details=_details(o))


def _audit(db: AsyncSession, admin_id: int, action: str, target_type: str, target_id: str, meta: dict) -> None:
    db.add(AuditLog(actor_telegram_id=admin_id, action=action, target_type=target_type,
                    target_id=target_id, safe_metadata=json.dumps(meta)))


@router.get("/me", summary="Check admin access")
async def me(admin_id: int = Depends(current_admin)):
    return {"admin": True, "telegram_id": admin_id}


@router.get("/orders", response_model=list[AdminOrderOut], summary="List orders")
async def list_orders(status: str | None = Query(default=None, max_length=32), limit: int = Query(default=50, ge=1, le=200),
                      offset: int = Query(default=0, ge=0), _: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    q = (select(Order, User, Product).join(User, Order.user_id == User.id)
         .join(Product, Order.product_id == Product.id).order_by(Order.created_at.desc()).limit(limit).offset(offset))
    if status:
        if status not in st.ALL_STATUSES:
            raise HTTPException(status_code=400, detail="Unknown status")
        q = q.where(Order.status == status)
    return [_admin_order(o, u, p) for o, u, p in (await db.execute(q)).all()]


@router.post("/orders/{order_id}/transition", response_model=AdminOrderOut, summary="Change order status")
async def transition(order_id: str, body: TransitionRequest, admin_id: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    order = (await db.execute(select(Order).where(Order.id == order_id).with_for_update())).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        await transition_order(db, order, body.to_status, admin_id, body.note, request_id=str(uuid.uuid4()))
    except st.InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    user = (await db.execute(select(User).where(User.id == order.user_id))).scalar_one()
    product = (await db.execute(select(Product).where(Product.id == order.product_id))).scalar_one()
    text = CUSTOMER_MESSAGES.get(body.to_status)
    if text:
        await send_telegram_message(user.telegram_id, f"Buyurtma #{order.id[:8]}: {text}")
    return _admin_order(order, user, product)


@router.get("/products", response_model=list[AdminProductOut], summary="All products incl. inactive")
async def all_products(_: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Product).order_by(Product.category, Product.price))).scalars().all())


@router.post("/products", response_model=AdminProductOut, status_code=201, summary="Create product")
async def create_product(body: ProductIn, admin_id: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    product = Product(**body.model_dump(), fulfilment_mode="manual")
    db.add(product)
    try:
        await db.flush()
        _audit(db, admin_id, "product.create", "product", str(product.id), {"code": body.code})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Product code already exists")
    return product


@router.patch("/products/{product_id}", response_model=AdminProductOut, summary="Edit product / price / visibility")
async def patch_product(product_id: int, body: ProductPatch, admin_id: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    changes = body.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(product, key, value)
    _audit(db, admin_id, "product.update", "product", str(product.id), {k: str(v) for k, v in changes.items() if k != "description"})
    await db.commit()
    return product


@router.get("/stats", summary="Order counts and confirmed revenue")
async def stats(_: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    by_status = {s: n for s, n in (await db.execute(select(Order.status, func.count()).group_by(Order.status))).all()}
    revenue = {c: str(a) for c, a in (await db.execute(select(LedgerEntry.currency, func.sum(LedgerEntry.amount)).group_by(LedgerEntry.currency))).all()}
    return {"orders_by_status": by_status, "net_revenue_by_currency": revenue}


@router.get("/audit", summary="Latest audit records")
async def audit(limit: int = Query(default=50, ge=1, le=200), _: int = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit))).scalars().all()
    return [{"id": r.id, "at": r.created_at, "actor": r.actor_telegram_id, "action": r.action,
             "target": f"{r.target_type}:{r.target_id}", "meta": r.safe_metadata} for r in rows]
