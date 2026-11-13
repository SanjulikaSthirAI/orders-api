import pytest


@pytest.mark.parametrize("payload", [{}], ids=["TC-2.1"])
def test_US2_AC_2_1_response_exposes_refunded_order_and_time(refund_client, assert_refunded, payload):
    client, order_id, _ = refund_client()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.is_success
    assert_refunded(response.json(), order_id)


@pytest.mark.parametrize("payload", [{}], ids=["TC-2.2"])
def test_US2_AC_2_2_retrieved_order_exposes_refunded_status_and_time(refund_client, assert_refunded, payload):
    client, order_id, _ = refund_client()
    assert client.post(f"/orders/{order_id}/refunds", json=payload).is_success
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert_refunded(response.json(), order_id)


@pytest.mark.parametrize("payload", [{"refund_time": "2025-01-20T00:00:00Z"}], ids=["TC-2.3"])
def test_US2_AC_2_3_client_time_does_not_replace_acceptance_time(refund_client, assert_refunded, payload):
    client, order_id, _ = refund_client()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.is_success
    assert_refunded(response.json(), order_id)
    assert_refunded(client.get(f"/orders/{order_id}").json(), order_id)
