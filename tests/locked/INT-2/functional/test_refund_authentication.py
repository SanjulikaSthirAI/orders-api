"""Public HTTP authentication precedes idempotency validation and order lookup."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


@pytest.mark.parametrize("headers", [{}, {"Idempotency-Key": "unauthenticated-001"}])
def test_US3_AC_5_1_unauthenticated_refund_is_rejected_before_other_validation(headers):
    with TestClient(create_app(OrderStore(orders=[]))) as client:
        response = client.post("/orders/ORD-9999/refunds", headers=headers)
    assert response.status_code == 401
