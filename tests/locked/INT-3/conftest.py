"""Runtime seam: approved refund HTTP endpoint using the existing app factory.

No support authorization marker is defined by the current API or approved TDD.
These cases exercise the HTTP behavior; authorization coverage remains blocked.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


@pytest.fixture
def refund_client():
    def build(created_at="2025-01-15T00:00:00Z", now="2025-01-31T12:00:00Z"):
        clock = [datetime.fromisoformat(created_at)]
        app = create_app(OrderStore(orders=[], clock=lambda: clock[0]))
        assert "/orders/{order_id}/refunds" in app.openapi()["paths"], "Refund endpoint is not implemented"
        client = TestClient(app)
        response = client.post("/orders", json={
            "customer_name": "Synthetic test customer",
            "items": [{"sku": "TEST-1", "name": "Test item", "quantity": 1, "unit_price_cents": 10000}],
        })
        assert response.status_code == 201
        clock[0] = datetime.fromisoformat(now)
        return client, response.json()["id"], clock

    return build


@pytest.fixture
def assert_refunded():
    def check(body, order_id, expected_time="2025-01-31T12:00:00Z"):
        assert body["id"] == order_id
        assert body["status"] == "refunded"
        assert datetime.fromisoformat(body["refund_time"]) == datetime.fromisoformat(expected_time)
        assert body["total_cents"] == 10000

    return check
