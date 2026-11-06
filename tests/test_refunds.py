"""Story US-1: refund a delivered order. Tests are named with the acceptance criterion they prove."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Order, OrderItem, OrderStatus
from app.store import OrderStore

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)
ITEM = OrderItem(sku="MUG-01", name="Enamel mug", quantity=2, unit_price_cents=1250)


def make_client(*orders: Order) -> TestClient:
    return TestClient(create_app(OrderStore(list(orders) or None, clock=lambda: NOW)))


def an_order(order_id: str, status: OrderStatus, delivered: str | None = "2026-10-20T12:00:00+00:00") -> Order:
    return Order(id=order_id, customer_name="Test Customer", items=[ITEM], total_cents=2500, status=status,
                 created_at=datetime.fromisoformat("2026-10-01T09:00:00+00:00"),
                 delivered_at=datetime.fromisoformat(delivered) if delivered else None)


@pytest.mark.parametrize("delivered", ["2026-11-04T09:00:00+00:00", "2026-10-16T09:00:00+00:00"])
def test_AC_1_1_delivered_order_within_30_days_is_refunded_in_full(delivered):
    client = make_client(an_order("ORD-2000", OrderStatus.delivered, delivered))
    r = client.post("/orders/ORD-2000/refunds")
    assert r.status_code == 201
    assert r.json()["order_id"] == "ORD-2000" and r.json()["amount_cents"] == 2500


@pytest.mark.parametrize("order_id", ["ORD-2001", "ORD-2003"])
def test_AC_1_2_refunded_order_cannot_be_refunded_again(order_id):
    client = make_client(an_order("ORD-2001", OrderStatus.delivered), an_order("ORD-2003", OrderStatus.delivered))
    assert client.post(f"/orders/{order_id}/refunds").status_code == 201  # the first refund really happens
    again = client.post(f"/orders/{order_id}/refunds")
    assert again.status_code == 409 and "already been refunded" in again.json()["detail"]
    assert client.get(f"/orders/{order_id}").json()["status"] == "refunded"


@pytest.mark.parametrize("delivered, accepted", [
    ("2026-10-06T09:00:00+00:00", True),
    ("2026-10-05T08:59:00+00:00", False),
])
def test_AC_1_3_refund_window_is_30_days_from_delivery(delivered, accepted):
    client = make_client(an_order("ORD-2002", OrderStatus.delivered, delivered))
    assert client.post("/orders/ORD-2002/refunds").status_code == (201 if accepted else 409)


@pytest.mark.parametrize("order_id", ["ORD-1003", "ORD-1004", "ORD-1005"])
def test_AC_1_4_order_that_is_not_delivered_cannot_be_refunded(order_id):
    r = make_client().post(f"/orders/{order_id}/refunds")
    assert r.status_code == 409 and "only delivered orders" in r.json()["detail"]


def test_AC_1_5_unknown_order_is_404():
    assert make_client().post("/orders/ORD-9/refunds").status_code == 404
