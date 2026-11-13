"""Test-environment workflow; this does not certify a deployed release or authorization."""

import pytest


@pytest.mark.parametrize("payload", [{}], ids=["TC-5.1"])
def test_US5_AC_1_1_AC_2_1_full_refund_workflow_uses_api(refund_client, assert_refunded, payload):
    client, order_id, _ = refund_client()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.is_success
    assert_refunded(response.json(), order_id)
    retrieved = client.get(f"/orders/{order_id}")
    assert retrieved.status_code == 200
    assert_refunded(retrieved.json(), order_id)
