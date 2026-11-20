from app.main import create_app


def test_US2_AC_3_1_order_contract_exposes_refund_fields():
    properties = create_app().openapi()['components']['schemas']['Order']['properties']
    assert {'refunded_amount_cents', 'refunded_at'} <= properties.keys()
