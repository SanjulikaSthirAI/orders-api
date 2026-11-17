from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.parametrize('age', [timedelta(days=29, hours=23, minutes=59, seconds=59)])
def test_US2_AC_1_1_AC_6_1_before_cutoff_records_refund(
    age, clock, create_order, refund_order, read_order, parse_time,
):
    clock.now -= age
    order = create_order()
    clock.now = datetime(2026, 1, 31, 12, tzinfo=UTC)
    refund_order(order)
    recorded = read_order(order)
    assert recorded['refunded'] is True
    assert parse_time(recorded['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)


def test_US2_AC_6_2_exact_30_day_cutoff_is_eligible(clock, create_order, refund_order, read_order, parse_time):
    clock.now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    order = create_order()
    clock.now = datetime(2026, 1, 31, 12, tzinfo=UTC)
    refund_order(order)
    recorded = read_order(order)
    assert recorded['refunded'] is True
    assert parse_time(recorded['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)


def test_US2_AC_1_2_response_matches_recorded_processing_time(create_order, refund_order, read_order, parse_time):
    order = create_order()
    response = refund_order(order)
    recorded = read_order(order)
    assert parse_time(response['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)
    assert recorded['refund_time'] == response['refund_time']


def test_US2_AC_1_3_supplied_refund_time_is_ignored(client, create_order, read_order, parse_time):
    order = create_order()
    response = client.post(f"/orders/{order['id']}/refunds", json={'refund_time': '1999-01-01T00:00:00Z'})
    assert response.status_code == 200, response.text
    assert parse_time(response.json()['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)
    assert parse_time(read_order(order)['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)


def test_US2_AC_1_4_refund_accepts_no_request_body(client, create_order, read_order):
    order = create_order()
    response = client.post(f"/orders/{order['id']}/refunds")
    assert response.status_code == 200, response.text
    assert read_order(order)['refunded'] is True


def test_US2_AC_2_1_success_identifies_order_and_refund(create_order, refund_order, parse_time):
    order = create_order()
    response = refund_order(order)
    assert response['id'] == order['id']
    assert response['refunded'] is True
    assert parse_time(response['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)


def test_US2_AC_9_4_read_exposes_recorded_refund(create_order, refund_order, read_order, parse_time):
    order = create_order()
    refund_order(order)
    recorded = read_order(order)
    assert recorded['refunded'] is True
    assert parse_time(recorded['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)


def test_US2_AC_9_5_list_exposes_recorded_refund(create_order, refund_order, listed_order, parse_time):
    order = create_order()
    refund_order(order)
    recorded = listed_order(order)
    assert recorded['refunded'] is True
    assert parse_time(recorded['refund_time']) == datetime(2026, 1, 31, 12, tzinfo=UTC)


@pytest.mark.parametrize('surface', ['refund', 'read', 'list'])
def test_US2_AC_9_7_refunded_responses_are_not_cancelled(
    surface, create_order, refund_order, read_order, listed_order,
):
    order = create_order()
    response = refund_order(order)
    if surface == 'read':
        response = read_order(order)
    elif surface == 'list':
        response = listed_order(order)
    assert response['refunded'] is True
    assert response['status'] == 'placed'
