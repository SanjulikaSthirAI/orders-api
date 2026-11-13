"""Eligibility observed through HTTP; the TDD defines no store refund signature."""

import pytest


@pytest.mark.parametrize("created_at", ["2025-01-02T12:00:00Z"], ids=["TC-1.1"])
def test_US1_AC_1_1_records_refund_after_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at)
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id)
    assert_refunded(client.get(f"/orders/{order_id}").json(), order_id)


@pytest.mark.parametrize("created_at", ["2025-01-01T12:00:00Z"], ids=["TC-1.2"])
def test_US1_AC_1_2_records_refund_exactly_at_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at)
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id)


@pytest.mark.parametrize("created_at", ["2025-03-01T00:30:00Z", "2025-03-01T00:30:01Z"],
                         ids=["TC-1.7-at", "TC-1.7-after"])
def test_US1_AC_5_2_utc_boundary_allows_at_and_after_cutoff(refund_client, assert_refunded, created_at):
    client, order_id, _ = refund_client(created_at, now="2025-03-31T00:30:00Z")
    response = client.post(f"/orders/{order_id}/refunds", json={})
    assert response.is_success
    assert_refunded(response.json(), order_id, "2025-03-31T00:30:00Z")


@pytest.mark.parametrize("payload", [{"refund_time": "2025-01-20T00:00:00Z"}], ids=["TC-1.3"])
def test_US1_AC_2_3_uses_acceptance_time_instead_of_client_time(refund_client, assert_refunded, payload):
    client, order_id, _ = refund_client()
    response = client.post(f"/orders/{order_id}/refunds", json=payload)
    assert response.is_success
    assert_refunded(response.json(), order_id)
    assert_refunded(client.get(f"/orders/{order_id}").json(), order_id)
