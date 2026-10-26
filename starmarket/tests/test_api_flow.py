"""End-to-end API flow on a temporary SQLite database (requires the project dependencies)."""
import pytest
from fastapi.testclient import TestClient

from conftest import make_init_data


@pytest.fixture(scope="module")
def client():
    from app.api.routes import admin as admin_routes

    async def _no_network(chat_id, text):
        return True

    admin_routes.send_telegram_message = _no_network
    from app.main import app
    with TestClient(app) as c:
        yield c


def login(client, tg_id, name="User"):
    r = client.post("/api/v1/auth/telegram", json={"init_data": make_init_data({"id": tg_id, "first_name": name})})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()


def test_full_order_lifecycle(client):
    cust, cust_info = login(client, 111, "Ali")
    admin, admin_info = login(client, 999, "Boss")
    assert cust_info["user"]["is_admin"] is False and admin_info["user"]["is_admin"] is True

    # customers cannot reach admin endpoints
    assert client.get("/api/v1/admin/orders", headers=cust).status_code == 403
    assert client.get("/api/v1/admin/orders").status_code == 401

    # admin creates an inactive product; it is hidden until activated
    p = client.post("/api/v1/admin/products", headers=admin, json={
        "code": "stars_100", "category": "stars", "name_uz": "100 Stars", "name_ru": "100 Stars",
        "name_en": "100 Stars", "amount": 100, "price": "25000"})
    assert p.status_code == 201, p.text
    pid = p.json()["id"]
    assert client.get("/api/v1/products").json() == []
    assert client.post("/api/v1/orders", headers=cust, json={
        "product_id": pid, "customer_details": {"telegram_username": "@ali_vali"},
        "idempotency_key": "inactive-product-key-1"}).status_code == 404
    assert client.patch(f"/api/v1/admin/products/{pid}", headers=admin, json={"is_active": True}).status_code == 200
    assert len(client.get("/api/v1/products").json()) == 1

    # order creation: server-side price, validation, idempotency
    body = {"product_id": pid, "quantity": 2, "customer_details": {"telegram_username": "ali_vali"},
            "idempotency_key": "order-key-0000001"}
    r = client.post("/api/v1/orders", headers=cust, json=body)
    assert r.status_code == 201, r.text
    order = r.json()
    assert float(order["total_amount"]) == 50000 and order["status"] == "AWAITING_PAYMENT"
    again = client.post("/api/v1/orders", headers=cust, json=body)
    assert again.json()["id"] == order["id"]
    assert client.post("/api/v1/orders", headers=cust, json={**body, "customer_details": {"password": "x"}, "idempotency_key": "order-key-0000002"}).status_code == 422
    assert client.post("/api/v1/orders", headers=admin, json=body).status_code == 409  # key owned by another user

    # a different user cannot read the order
    other, _ = login(client, 222, "Vali")
    assert client.get(f"/api/v1/orders/{order['id']}", headers=other).status_code == 404

    # invalid shortcut is rejected; valid path works; money recorded exactly once
    oid = order["id"]
    t = lambda to: client.post(f"/api/v1/admin/orders/{oid}/transition", headers=admin, json={"to_status": to})  # noqa: E731
    assert t("PAID").status_code == 409
    assert client.post(f"/api/v1/admin/orders/{oid}/transition", headers=cust, json={"to_status": "PAID"}).status_code == 403
    for to in ("PAYMENT_SUBMITTED", "PAID", "PROCESSING", "COMPLETED"):
        assert t(to).status_code == 200, to
    assert t("PAID").status_code == 409
    assert t("REFUND_PENDING").status_code == 409  # completed orders are final
    stats = client.get("/api/v1/admin/stats", headers=admin).json()
    assert stats["orders_by_status"]["COMPLETED"] == 1
    assert float(stats["net_revenue_by_currency"]["UZS"]) == 50000
    assert any(a["action"] == "order.paid" for a in client.get("/api/v1/admin/audit", headers=admin).json())


def test_customer_cancel_and_refund_ledger(client):
    cust, _ = login(client, 333, "Sardor")
    admin, _ = login(client, 999)
    pid = client.get("/api/v1/products").json()[0]["id"]
    mk = lambda key: client.post("/api/v1/orders", headers=cust, json={  # noqa: E731
        "product_id": pid, "customer_details": {"telegram_username": "@sardor_x"}, "idempotency_key": key}).json()
    o1 = mk("cancel-key-000001")
    assert client.post(f"/api/v1/orders/{o1['id']}/cancel", headers=cust).json()["status"] == "CANCELLED"
    assert client.post(f"/api/v1/orders/{o1['id']}/cancel", headers=cust).status_code == 409
    o2 = mk("refund-key-000001")
    for to in ("PAYMENT_SUBMITTED", "PAID", "REFUND_PENDING", "REFUNDED"):
        assert client.post(f"/api/v1/admin/orders/{o2['id']}/transition", headers=admin, json={"to_status": to}).status_code == 200
    net = client.get("/api/v1/admin/stats", headers=admin).json()["net_revenue_by_currency"]["UZS"]
    assert float(net) == 50000  # first order's payment; the refunded order nets to zero


def test_bad_tokens_and_initdata(client):
    assert client.get("/api/v1/orders", headers={"Authorization": "Bearer abc.def"}).status_code == 401
    bad = make_init_data({"id": 5}, bot_token="999:OTHER")
    assert client.post("/api/v1/auth/telegram", json={"init_data": bad}).status_code == 401
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert "TEST-TOKEN" not in client.get("/api/v1/payment-info").text
