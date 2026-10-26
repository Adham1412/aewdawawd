from pydantic import ValidationError

from app.schemas.api import OrderCreate, ProductIn

KEY = "k" * 16


def _bad(**kw):
    try:
        OrderCreate(**kw)
    except ValidationError:
        return True
    return False


def test_username_is_normalised():
    o = OrderCreate(product_id=1, customer_details={"telegram_username": "ali_vali"}, idempotency_key=KEY)
    assert o.customer_details == {"telegram_username": "@ali_vali"}


def test_username_required_and_validated():
    assert _bad(product_id=1, idempotency_key=KEY)  # missing details
    assert _bad(product_id=1, customer_details={}, idempotency_key=KEY)
    assert _bad(product_id=1, customer_details={"telegram_username": "a b"}, idempotency_key=KEY)
    assert _bad(product_id=1, customer_details={"telegram_username": "ab"}, idempotency_key=KEY)


def test_password_or_code_fields_are_rejected():
    for field in ("password", "code", "sms_code", "login_code"):
        assert _bad(product_id=1, customer_details={"telegram_username": "@ali_vali", field: "123456"}, idempotency_key=KEY)


def test_quantity_and_key_limits():
    assert _bad(product_id=1, quantity=0, customer_details={"telegram_username": "@ali_vali"}, idempotency_key=KEY)
    assert _bad(product_id=1, quantity=101, customer_details={"telegram_username": "@ali_vali"}, idempotency_key=KEY)
    assert _bad(product_id=1, customer_details={"telegram_username": "@ali_vali"}, idempotency_key="short")


def test_product_validation():
    base = dict(code="stars_100", category="stars", name_uz="a", name_ru="a", name_en="a", amount=100, price="25000")
    ProductIn(**base)
    for patch in ({"price": "0"}, {"amount": 0}, {"category": "gifts"}, {"code": "Bad Code"}):
        try:
            ProductIn(**{**base, **patch})
        except ValidationError:
            continue
        raise AssertionError(f"accepted invalid product {patch}")
