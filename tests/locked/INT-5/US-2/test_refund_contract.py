from app.main import create_app


def test_US2_AC_3_1_order_contract_exposes_refund_fields():
    properties = create_app().openapi()['components']['schemas']['Order']['properties']
    assert {'refunded_amount_cents', 'refunded_at'} <= properties.keys()


def test_US2_AC_2_4_refund_contract_accepts_empty_body_without_reason():
    schema = create_app().openapi()
    operation = schema['paths']['/orders/{order_id}/refunds']['post']
    request_body = operation.get('requestBody')
    if request_body is None:
        return

    body_schema = request_body['content']['application/json']['schema']
    if '$ref' in body_schema:
        name = body_schema['$ref'].rsplit('/', 1)[-1]
        body_schema = schema['components']['schemas'][name]
    assert body_schema.get('type') == 'object'
    assert not body_schema.get('required', [])
