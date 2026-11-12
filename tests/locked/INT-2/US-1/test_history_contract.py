"""TC-1.3: internal refund history has no public retrieval interface."""

import pytest

from app.main import create_app
from app.store import OrderStore


@pytest.mark.parametrize("path", [
    "/refund-audit",
    "/refund-history",
    "/orders/{order_id}/refund-history",
    "/orders/{order_id}/refunds/history",
])
def test_US1_AC_9_4_no_refund_audit_history_retrieval(path):
    paths = create_app(OrderStore(orders=[])).openapi()["paths"]
    assert "get" not in paths.get(path, {})
