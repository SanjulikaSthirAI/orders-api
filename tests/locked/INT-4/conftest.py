"""Approved seam: HTTP Orders API; real store with its public injected clock."""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


@pytest.fixture
def clock():
    class Clock:
        now = datetime(2026, 1, 31, 12, tzinfo=UTC)

        def __call__(self):
            return self.now

    return Clock()


@pytest.fixture
def client(clock):
    with TestClient(create_app(OrderStore(orders=[], clock=clock))) as client:
        yield client


@pytest.fixture
def create_order(client):
    def create():
        response = client.post('/orders', json={
            'customer_name': 'Synthetic test customer',
            'items': [{'sku': 'TEST-01', 'name': 'Demo item', 'quantity': 1, 'unit_price_cents': 1250}],
        })
        assert response.status_code == 201, response.text
        return response.json()

    return create


@pytest.fixture
def refund_order(client):
    def refund(order):
        response = client.post(f"/orders/{order['id']}/refunds")
        assert response.status_code == 200, response.text
        return response.json()

    return refund


@pytest.fixture
def read_order(client):
    def read(order):
        response = client.get(f"/orders/{order['id']}")
        assert response.status_code == 200, response.text
        return response.json()

    return read


@pytest.fixture
def listed_order(client):
    def listed(order):
        response = client.get('/orders')
        assert response.status_code == 200, response.text
        return next(item for item in response.json() if item['id'] == order['id'])

    return listed


@pytest.fixture
def parse_time():
    return lambda value: datetime.fromisoformat(value.replace('Z', '+00:00'))
