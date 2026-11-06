from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


@pytest.fixture
def client():
    return TestClient(create_app(OrderStore(clock=lambda: NOW)))


ITEM = {"sku": "MUG-01", "name": "Enamel mug", "quantity": 2, "unit_price_cents": 1250}


def test_list_is_newest_first(client):
    ids = [o["id"] for o in client.get("/orders").json()]
    assert ids == ["ORD-1004", "ORD-1003", "ORD-1005", "ORD-1002", "ORD-1001"]


def test_list_filters_by_status(client):
    delivered = client.get("/orders", params={"status": "delivered"}).json()
    assert [o["id"] for o in delivered] == ["ORD-1002", "ORD-1001"]
    assert all(o["delivered_at"] for o in delivered)


def test_list_rejects_an_unknown_status(client):
    assert client.get("/orders", params={"status": "lost"}).status_code == 422


def test_get_returns_the_order_with_its_total(client):
    order = client.get("/orders/ORD-1002").json()
    assert order["customer_name"] == "Ben Carter" and order["total_cents"] == 3890 + 3 * 640


def test_get_unknown_order_is_404(client):
    r = client.get("/orders/ORD-9")
    assert r.status_code == 404 and r.json() == {"detail": "Order ORD-9 not found"}


def test_place_order_computes_total_and_starts_placed(client):
    r = client.post("/orders", json={"customer_name": "Farah Khan", "items": [ITEM]})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == "ORD-1006" and body["status"] == "placed" and body["total_cents"] == 2500
    assert body["created_at"].startswith("2026-11-05T09:00:00") and body["delivered_at"] is None
    assert client.get("/orders/ORD-1006").json() == body


@pytest.mark.parametrize("payload", [
    {"customer_name": "", "items": [ITEM]},
    {"customer_name": "Farah Khan", "items": []},
    {"customer_name": "Farah Khan", "items": [{**ITEM, "quantity": 0}]},
    {"customer_name": "Farah Khan", "items": [{**ITEM, "unit_price_cents": -1}]},
])
def test_place_order_validates_input(client, payload):
    assert client.post("/orders", json=payload).status_code == 422


def test_cancel_a_placed_order(client):
    r = client.post("/orders/ORD-1004/cancel")
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert client.get("/orders/ORD-1004").json()["status"] == "cancelled"


@pytest.mark.parametrize("order_id, status", [("ORD-1003", "shipped"), ("ORD-1001", "delivered"),
                                              ("ORD-1005", "cancelled")])
def test_only_placed_orders_can_be_cancelled(client, order_id, status):
    r = client.post(f"/orders/{order_id}/cancel")
    assert r.status_code == 409 and status in r.json()["detail"]
    assert client.get(f"/orders/{order_id}").json()["status"] == status


def test_cancel_unknown_order_is_404(client):
    assert client.post("/orders/ORD-9/cancel").status_code == 404
