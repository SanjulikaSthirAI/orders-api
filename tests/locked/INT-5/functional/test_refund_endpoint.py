from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


def test_unauthenticated_refund_is_rejected():
    client = TestClient(create_app(OrderStore()))
    response = client.post('/orders/ORD-1004/refunds', headers={'Idempotency-Key': 'key-1'}, json={})
    assert response.status_code == 401


def test_refund_contract_requires_idempotency_key_and_declares_errors():
    operation = create_app().openapi()['paths']['/orders/{order_id}/refunds']['post']
    assert any(
        parameter['in'] == 'header'
        and parameter['name'].lower() == 'idempotency-key'
        and parameter['required'] is True
        for parameter in operation['parameters']
    )
    assert {'401', '403', '404', '409', '422', '503'} <= operation['responses'].keys()
