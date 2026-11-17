from datetime import UTC, datetime, timedelta

import pytest


def assert_rejection(response, detail, status=409):
    assert response.status_code == status, response.text
    assert response.json() == {'detail': detail}


def test_US3_AC_3_1_unknown_refund_returns_exact_not_found(client):
    assert_rejection(client.post('/orders/missing-order/refunds'), 'order not found', 404)


def test_US3_AC_3_2_unknown_refund_does_not_create_order(client):
    assert client.get('/orders/missing-order').status_code == 404
    assert_rejection(client.post('/orders/missing-order/refunds'), 'order not found', 404)
    assert client.get('/orders/missing-order').status_code == 404
    assert client.get('/orders').json() == []


def test_US3_AC_4_1_repeat_refund_is_conflict(client, create_order, refund_order):
    order = create_order()
    refund_order(order)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'order already refunded')


@pytest.mark.parametrize('surface', ['read', 'list'])
def test_US3_AC_4_2_repeat_preserves_original_refund_time(
    surface, client, clock, create_order, refund_order, read_order, listed_order, parse_time,
):
    clock.now = datetime(2026, 1, 1, 10, tzinfo=UTC)
    order = create_order()
    refund_order(order)
    before = read_order(order)
    clock.now = datetime(2026, 1, 2, 10, tzinfo=UTC)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'order already refunded')
    after = read_order(order) if surface == 'read' else listed_order(order)
    assert after == before
    assert parse_time(after['refund_time']) == datetime(2026, 1, 1, 10, tzinfo=UTC)


def test_US3_AC_5_1_cancelled_order_refund_is_conflict(client, create_order):
    order = create_order()
    assert client.post(f"/orders/{order['id']}/cancel").status_code == 200
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'order cancelled')


def test_US3_AC_5_2_cancelled_refund_rejection_preserves_order(client, create_order, read_order):
    order = create_order()
    assert client.post(f"/orders/{order['id']}/cancel").status_code == 200
    before = read_order(order)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'order cancelled')
    after = read_order(order)
    assert after == before
    assert after['status'] == 'cancelled'
    assert after['refunded'] is False
    assert after['refund_time'] is None


def test_US3_AC_6_3_one_second_after_cutoff_is_expired(client, clock, create_order):
    order = create_order()
    clock.now += timedelta(days=30, seconds=1)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'refund window expired')


def test_US3_AC_6_4_expired_refund_rejection_preserves_order(client, clock, create_order, read_order):
    order = create_order()
    before = read_order(order)
    clock.now += timedelta(days=30, seconds=1)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'refund window expired')
    after = read_order(order)
    assert after == before
    assert after['refunded'] is False
    assert after['refund_time'] is None


def test_US3_AC_7_1_already_refunded_takes_priority_over_expired(
    client, clock, create_order, refund_order, read_order,
):
    order = create_order()
    refund_order(order)
    before = read_order(order)
    clock.now += timedelta(days=30, seconds=1)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'order already refunded')
    assert read_order(order) == before


def test_US3_AC_7_2_cancelled_takes_priority_over_expired(client, clock, create_order, read_order):
    order = create_order()
    assert client.post(f"/orders/{order['id']}/cancel").status_code == 200
    before = read_order(order)
    clock.now += timedelta(days=30, seconds=1)
    assert_rejection(client.post(f"/orders/{order['id']}/refunds"), 'order cancelled')
    assert read_order(order) == before
