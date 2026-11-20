from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


def test_US1_AC_1_1_order_exposes_refund_availability_reason():
    client = TestClient(create_app(OrderStore()))
    response = client.get('/orders/ORD-1005')

    assert response.status_code == 200
    assert 'refund_unavailable_reason' in response.json()


def test_US1_AC_1_4_order_status_contract_includes_refunded():
    schema = create_app().openapi()['components']['schemas']['OrderStatus']
    assert 'refunded' in schema['enum']


def test_US1_AC_1_2_cancelled_order_has_not_paid_refund_reason():
    client = TestClient(create_app(OrderStore()))

    response = client.get('/orders/ORD-1005')

    assert response.status_code == 200
    assert response.json()['refund_unavailable_reason'] == 'not_paid'
