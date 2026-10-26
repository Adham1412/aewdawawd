"""Order status machine (stdlib only, so it can be tested without any dependency)."""

AWAITING_PAYMENT = "AWAITING_PAYMENT"
PAYMENT_SUBMITTED = "PAYMENT_SUBMITTED"  # customer sent a receipt; admin must verify the money
PAID = "PAID"
PROCESSING = "PROCESSING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
REFUND_PENDING = "REFUND_PENDING"
REFUNDED = "REFUNDED"

TRANSITIONS: dict[str, frozenset[str]] = {
    AWAITING_PAYMENT: frozenset({PAYMENT_SUBMITTED, CANCELLED}),
    PAYMENT_SUBMITTED: frozenset({PAID, AWAITING_PAYMENT, CANCELLED}),
    PAID: frozenset({PROCESSING, REFUND_PENDING}),
    PROCESSING: frozenset({COMPLETED, FAILED}),
    FAILED: frozenset({PROCESSING, REFUND_PENDING}),
    REFUND_PENDING: frozenset({REFUNDED}),
    COMPLETED: frozenset(),
    CANCELLED: frozenset(),
    REFUNDED: frozenset(),
}
ALL_STATUSES = frozenset(TRANSITIONS)
# Only these may be set by the customer; everything else needs an administrator.
CUSTOMER_TRANSITIONS = frozenset({(AWAITING_PAYMENT, CANCELLED), (AWAITING_PAYMENT, PAYMENT_SUBMITTED)})
OPEN_STATUSES = frozenset({AWAITING_PAYMENT, PAYMENT_SUBMITTED, PAID, PROCESSING, FAILED, REFUND_PENDING})


class InvalidTransition(ValueError):
    pass


def check_transition(current: str, target: str) -> None:
    if current not in TRANSITIONS or target not in ALL_STATUSES:
        raise InvalidTransition("Unknown order status")
    if target not in TRANSITIONS[current]:
        raise InvalidTransition(f"Transition {current} -> {target} is not allowed")


STATUS_TEXT_UZ = {
    AWAITING_PAYMENT: "To'lov kutilmoqda",
    PAYMENT_SUBMITTED: "Chek tekshirilmoqda",
    PAID: "To'lov tasdiqlandi",
    PROCESSING: "Bajarilmoqda",
    COMPLETED: "Bajarildi",
    FAILED: "Muammo yuz berdi, admin ko'rib chiqmoqda",
    CANCELLED: "Bekor qilindi",
    REFUND_PENDING: "Pul qaytarilmoqda",
    REFUNDED: "Pul qaytarildi",
}
