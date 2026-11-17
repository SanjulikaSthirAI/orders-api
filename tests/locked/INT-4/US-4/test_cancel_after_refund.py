import pytest


def test_US4_AC_8_1_cancel_refunded_order_returns_conflict(client, create_order, refund_order):
    order = create_order()
    refund_order(order)
    response = client.post(f"/orders/{order['id']}/cancel")
    assert response.status_code == 409
    assert response.json() == {'detail': 'order already refunded'}


def test_US4_AC_8_2_cancel_rejection_preserves_refunded_order(client, create_order, refund_order, read_order):
    order = create_order()
    refund_order(order)
    before = read_order(order)
    response = client.post(f"/orders/{order['id']}/cancel")
    assert response.status_code == 409
    assert response.json() == {'detail': 'order already refunded'}
    after = read_order(order)
    assert after == before
    assert after['refunded'] is True
    assert after['status'] == 'placed'
    assert after['refund_time'] == before['refund_time']


@pytest.mark.parametrize('surface', ['cancel', 'read'])
def test_US4_AC_9_7_rejected_cancel_does_not_create_conflicting_state(
    surface, client, create_order, refund_order, read_order,
):
    order = create_order()
    refund_order(order)
    response = client.post(f"/orders/{order['id']}/cancel")
    assert response.status_code == 409
    if surface == 'cancel':
        assert response.json() == {'detail': 'order already refunded'}
    recorded = read_order(order)
    assert recorded['refunded'] is True
    assert recorded['status'] == 'placed'
