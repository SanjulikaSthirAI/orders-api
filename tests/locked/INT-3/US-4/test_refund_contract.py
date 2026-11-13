"""INT-3 US-4: inspect the published OpenAPI boundary, not app internals.

The approved TC-4 cases confirm this seam. Runtime cases need the unresolved
store, authorization and error-response contracts before they can be authored.
"""

from pathlib import Path

import pytest
import yaml

CONTRACT = Path(__file__).resolve().parents[4] / "openapi.yaml"
REFUND_PATH = "/orders/{order_id}/refunds"


@pytest.fixture
def contract():
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def resolve(contract, schema):
    """Follow local OpenAPI references without assuming component names."""
    while "$ref" in schema:
        reference = schema["$ref"]
        assert reference.startswith("#/"), "The published schema must resolve locally"
        schema = contract
        for part in reference[2:].split("/"):
            schema = schema[part.replace("~1", "/").replace("~0", "~")]
    return schema


def alternatives(contract, schema):
    schema = resolve(contract, schema)
    yield schema
    for keyword in ("anyOf", "oneOf", "allOf"):
        for child in schema.get(keyword, []):
            yield from alternatives(contract, child)


def properties(contract, schema):
    result = {}
    for variant in alternatives(contract, schema):
        result.update(variant.get("properties", {}))
    return result


def assert_refunded_order_schema(contract, schema):
    fields = properties(contract, schema)
    assert "status" in fields, "The updated Order must expose its status"
    statuses = {
        value
        for variant in alternatives(contract, fields["status"])
        for value in variant.get("enum", [])
    }
    assert "refunded" in statuses
    assert "refund_time" in fields, "The Order contract must expose Refund time"
    assert any(
        variant.get("type") == "string" and variant.get("format") == "date-time"
        for variant in alternatives(contract, fields["refund_time"])
    ), "Refund time must be a date-time, optionally nullable for non-refunded Orders"


@pytest.mark.parametrize("path,method", [(REFUND_PATH, "post")], ids=["TC-4.1"])
def test_US4_AC_1_1_openapi_declares_refund_success_with_refunded_order(contract, path, method):
    assert path in contract["paths"], "The published contract lacks the refund endpoint"
    operation = contract["paths"][path][method]
    successes = [response for code, response in operation["responses"].items() if str(code).startswith("2")]
    assert successes, "Refund recording must declare a success response"
    for response in successes:
        response = resolve(contract, response)
        assert_refunded_order_schema(contract, response["content"]["application/json"]["schema"])


@pytest.mark.parametrize("path,method", [("/orders/{order_id}", "get")], ids=["TC-4.2"])
def test_US4_AC_2_2_openapi_declares_retrieved_order_refund_fields(contract, path, method):
    response = resolve(contract, contract["paths"][path][method]["responses"]["200"])
    assert_refunded_order_schema(contract, response["content"]["application/json"]["schema"])


@pytest.mark.parametrize(
    "reason_code",
    ["ORDER_ALREADY_REFUNDED", "ORDER_CANCELLED", "ORDER_TOO_OLD", "ORDER_NOT_FOUND"],
    ids=["TC-4.3-already-refunded", "TC-4.3-cancelled", "TC-4.3-too-old", "TC-4.3-not-found"],
)
def test_US4_AC_3_1_AC_4_1_AC_5_1_AC_7_1_openapi_declares_refund_reason_and_message(contract, reason_code):
    assert REFUND_PATH in contract["paths"], "The published contract lacks the refund endpoint"
    responses = contract["paths"][REFUND_PATH]["post"]["responses"]
    matching_schemas = []
    for code, response in responses.items():
        if not str(code).startswith("4"):
            continue
        response = resolve(contract, response)
        schema = response.get("content", {}).get("application/json", {}).get("schema", {})
        for variant in alternatives(contract, schema):
            fields = properties(contract, variant)
            codes = {
                value
                for code_schema in alternatives(contract, fields.get("reason_code", {}))
                for value in code_schema.get("enum", [])
            }
            if reason_code in codes:
                matching_schemas.append(variant)
    assert matching_schemas, f"No error response declares stable reason code {reason_code}"
    for schema in matching_schemas:
        fields = properties(contract, schema)
        required = {name for variant in alternatives(contract, schema) for name in variant.get("required", [])}
        assert {"reason_code", "message"} <= required
        message = resolve(contract, fields["message"])
        assert message.get("type") == "string"
        assert message.get("minLength", 0) >= 1, "The contract must require a non-empty message"
