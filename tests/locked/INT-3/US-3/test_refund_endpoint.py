import pytest


@pytest.mark.parametrize("created_at", ["2025-01-02T12:00:00Z"], ids=["TC-3.1"])
def test_US3_AC_1_1_AC_2_1_endpoint_returns_updated_order(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at)
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id)


@pytest.mark.parametrize("created_at", ["2025-01-01T12:00:00Z"], ids=["TC-3.2"])
def test_US3_AC_1_2_endpoint_accepts_exact_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at)
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id)


@pytest.mark.parametrize("payload", [{"amount": 1000}], ids=["TC-3.6-cents"])
def test_US3_AC_8_1_partial_request_is_rejected_without_refunding(refund_client, payload):
    client, order_id, _ = refund_client()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.status_code == 422
    retrieved = client.get(f"/orders/{order_id}")
    assert retrieved.status_code == 200
    assert retrieved.json()["status"] == "placed"
    assert retrieved.json().get("refund_time") is None


@pytest.mark.parametrize("created_at", ["2025-01-15T00:00:00Z"], ids=["TC-3.4"])
def test_US3_AC_3_2_repeated_request_is_conflict_and_preserves_first_refund(
    refund_client, assert_refunded, created_at,
):
    client, order_id, clock = refund_client(created_at)
    first = client.post(f"/orders/{order_id}/refunds", json={})
    assert first.is_success
    assert_refunded(first.json(), order_id)
    clock[0] = clock[0].fromisoformat("2025-01-31T12:05:00Z")
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 409
    assert response.json()["reason_code"] == "ORDER_ALREADY_REFUNDED"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").json() == first.json()


@pytest.mark.parametrize("order_id", ["ord-missing"], ids=["TC-3.5"])
def test_US3_AC_7_1_missing_order_returns_not_found_reason(refund_client, order_id):
    client, _, _ = refund_client()
    before = client.get("/orders").json()
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 404
    assert response.json()["reason_code"] == "ORDER_NOT_FOUND"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").status_code == 404
    assert client.get("/orders").json() == before
