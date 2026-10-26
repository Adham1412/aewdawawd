"""Order transitions with audit trail and ledger entries (one DB transaction each)."""
import json

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, LedgerEntry, Order
from app.services import order_states as st


async def transition_order(
    db: AsyncSession,
    order: Order,
    to_status: str,
    actor_telegram_id: int | None,
    note: str = "",
    request_id: str | None = None,
) -> None:
    """Move an order to a new status. Raises InvalidTransition; commits on success."""
    previous = order.status
    st.check_transition(previous, to_status)
    order.status = to_status
    # Ledger is append-only; the unique `reference` makes these writes idempotent.
    if to_status == st.PAID:
        db.add(LedgerEntry(user_id=order.user_id, order_id=order.id, entry_type="PAYMENT",
                           amount=order.total_amount, currency=order.currency,
                           reference=f"order:{order.id}:payment"))
    elif to_status == st.REFUNDED:
        db.add(LedgerEntry(user_id=order.user_id, order_id=order.id, entry_type="REFUND",
                           amount=-order.total_amount, currency=order.currency,
                           reference=f"order:{order.id}:refund"))
    db.add(AuditLog(actor_telegram_id=actor_telegram_id, action=f"order.{to_status.lower()}",
                    target_type="order", target_id=order.id, request_id=request_id,
                    safe_metadata=json.dumps({"from": previous, "note": note[:200]})))
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise st.InvalidTransition("Duplicate financial entry; order was already processed") from exc
