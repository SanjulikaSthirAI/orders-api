import pytest


def assert_defaults(order):
    assert order['refunded'] is False
    assert order['refund_time'] is None


def test_US1_AC_9_1_create_includes_default_refund_fields(create_order):
    assert_defaults(create_order())


def test_US1_AC_9_2_read_includes_default_refund_fields(create_order, read_order):
    assert_defaults(read_order(create_order()))


def test_US1_AC_9_3_list_includes_default_refund_fields(create_order, listed_order):
    assert_defaults(listed_order(create_order()))


def test_US1_AC_9_6_cancel_success_includes_refund_fields(client, create_order):
    order = create_order()
    response = client.post(f"/orders/{order['id']}/cancel")
    assert response.status_code == 200
    assert response.json()['status'] == 'cancelled'
    assert_defaults(response.json())


@pytest.mark.parametrize('surface', ['create', 'read', 'list', 'cancel'])
def test_US1_AC_9_7_existing_responses_preserve_state_invariant(
    surface, client, create_order, read_order, listed_order,
):
    order = create_order()
    if surface == 'read':
        order = read_order(order)
    elif surface == 'list':
        order = listed_order(order)
    elif surface == 'cancel':
        response = client.post(f"/orders/{order['id']}/cancel")
        assert response.status_code == 200
        order = response.json()
    assert_defaults(order)
    assert order['status'] == ('cancelled' if surface == 'cancel' else 'placed')
