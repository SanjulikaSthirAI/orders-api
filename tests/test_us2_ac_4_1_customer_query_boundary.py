from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


def test_US2_AC_4_1_customer_query_accepts_100_characters():
    client = TestClient(create_app(OrderStore(orders=[])))
    response = client.get('/orders', params={'customer': 'a' * 100})
    assert response.status_code == 200
    assert response.json() == []


def test_US2_AC_4_1_customer_query_rejects_more_than_100_characters():
    client = TestClient(create_app(OrderStore(orders=[])))
    response = client.get('/orders', params={'customer': 'a' * 101})
    assert response.status_code == 422
