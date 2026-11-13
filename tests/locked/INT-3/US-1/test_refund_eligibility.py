"""Eligibility observed through HTTP; the TDD defines no store refund signature."""

import pytest


@pytest.mark.parametrize("created_at", ["2025-01-02T12:00:00Z"], ids=["TC-1.1"])
def test_US_1_AC_1_1_records_refund_after_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at)
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id)
    assert_refunded(client.get(f"/orders/{order_id}").json(), order_id)


@pytest.mark.parametrize("created_at", ["2025-01-01T12:00:00Z"], ids=["TC-1.2"])
def test_US_1_AC_1_2_records_refund_exactly_at_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at)
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id)


@pytest.mark.parametrize("created_at", ["2025-03-01T00:30:00Z", "2025-03-01T00:30:01Z"],
                         ids=["TC-1.7-at", "TC-1.7-after"])
def test_US_1_AC_5_2_utc_boundary_allows_at_and_after_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at, now="2025-03-31T00:30:00Z")
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id, "2025-03-31T00:30:00Z")


@pytest.mark.parametrize("payload", [{"refund_time": "2025-01-20T00:00:00Z"}], ids=["TC-1.3"])
def test_US_1_AC_2_3_uses_acceptance_time_instead_of_client_time(refund_client, assert_refunded, payload):
    client, order_id, _ = refund_client()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.is_success
    assert_refunded(response.json(), order_id)
    assert_refunded(client.get(f"/orders/{order_id}").json(), order_id)


@pytest.mark.parametrize("created_at", ["2025-01-15T00:00:00Z"], ids=["TC-1.4"])
def test_US_1_AC_3_1_duplicate_preserves_original_refund(refund_client, assert_refunded, created_at):
    client, order_id, clock = refund_client(created_at, now="2025-01-20T00:00:00Z")
    first = client.post(f"/orders/{order_id}/refunds", json={})
    assert first.is_success
    clock[0] = clock[0].fromisoformat("2025-01-31T12:00:00Z")
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 409
    assert response.json()["reason_code"] == "ORDER_ALREADY_REFUNDED"
    assert response.json()["message"].strip()
    assert_refunded(client.get(f"/orders/{order_id}").json(), order_id, "2025-01-20T00:00:00Z")


@pytest.mark.parametrize("created_at", ["2025-01-15T00:00:00Z"], ids=["TC-1.5"])
def test_US_1_AC_4_1_cancelled_order_is_not_refunded(refund_client, created_at):
    client, order_id, _ = refund_client(created_at)
    assert client.post(f"/orders/{order_id}/cancel").status_code == 200
    before = client.get(f"/orders/{order_id}").json()
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 409
    assert response.json()["reason_code"] == "ORDER_CANCELLED"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").json() == before


@pytest.mark.parametrize("created_at", ["2025-01-01T11:59:59Z"], ids=["TC-1.6"])
def test_US_1_AC_5_1_before_cutoff_is_not_refunded(refund_client, created_at):
    client, order_id, _ = refund_client(created_at)
    before = client.get(f"/orders/{order_id}").json()
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 409
    assert response.json()["reason_code"] == "ORDER_TOO_OLD"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").json() == before


@pytest.mark.parametrize("created_at", ["2024-12-31T12:00:00Z"], ids=["TC-1.9"])
def test_US_1_AC_6_2_already_refunded_has_priority_over_age(refund_client, created_at):
    client, order_id, clock = refund_client(created_at, now="2025-01-20T00:00:00Z")
    assert client.post(f"/orders/{order_id}/refunds", json={}).is_success
    before = client.get(f"/orders/{order_id}").json()
    clock[0] = clock[0].fromisoformat("2025-01-31T12:00:00Z")
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 409
    assert response.json()["reason_code"] == "ORDER_ALREADY_REFUNDED"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").json() == before


@pytest.mark.parametrize("created_at", ["2024-12-31T12:00:00Z"], ids=["TC-1.10"])
def test_US_1_AC_6_3_cancelled_has_priority_over_age(refund_client, created_at):
    client, order_id, _ = refund_client(created_at)
    assert client.post(f"/orders/{order_id}/cancel").status_code == 200
    before = client.get(f"/orders/{order_id}").json()
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 409
    assert response.json()["reason_code"] == "ORDER_CANCELLED"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").json() == before


@pytest.mark.parametrize("order_id", ["ord-missing"], ids=["TC-1.11"])
def test_US_1_AC_7_1_missing_order_returns_reason_without_creating_order(refund_client, order_id):
    client, _, _ = refund_client()
    before = client.get("/orders").json()
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.status_code == 404
    assert response.json()["reason_code"] == "ORDER_NOT_FOUND"
    assert response.json()["message"].strip()
    assert client.get(f"/orders/{order_id}").status_code == 404
    assert client.get("/orders").json() == before


@pytest.mark.parametrize("payload", [{"amount": 1000}], ids=["TC-1.12-cents"])
def test_US_1_AC_8_1_partial_refund_is_rejected_without_mutation(refund_client, payload):
    client, order_id, _ = refund_client()
    before = client.get(f"/orders/{order_id}").json()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.status_code == 422
    assert client.get(f"/orders/{order_id}").json() == before
