"""Refund HTTP contracts; no invented service or authentication interfaces."""

from pathlib import Path

import pytest
import yaml

from app.main import create_app
from app.store import OrderStore


@pytest.fixture(params=["application", "published"])
def contract(request):
    if request.param == "application":
        return create_app(OrderStore(orders=[])).openapi()
    root = Path(__file__).resolve().parents[4]
    return yaml.safe_load((root / "openapi.yaml").read_text(encoding="utf-8"))


def refund_operation(contract):
    paths = contract["paths"]
    assert "/orders/{order_id}/refunds" in paths, "The approved refund operation is missing"
    assert "post" in paths["/orders/{order_id}/refunds"]
    return paths["/orders/{order_id}/refunds"]["post"]


def resolve_schema(contract, schema):
    if "$ref" in schema:
        for component in schema["$ref"].removeprefix("#/").split("/"):
            contract = contract[component]
        return contract
    return schema


def test_US3_AC_2_2_success_response_contains_only_timestamp_and_integer_cents(contract):
    """TC-3.1: the success schema exposes only the two approved refund fields."""
    operation = refund_operation(contract)
    assert "201" in operation["responses"]
    schema = resolve_schema(
        contract, operation["responses"]["201"]["content"]["application/json"]["schema"]
    )
    assert set(schema["properties"]) == {"refund_timestamp", "refund_amount_cents"}
    assert set(schema["required"]) == {"refund_timestamp", "refund_amount_cents"}
    assert schema["properties"]["refund_timestamp"]["type"] == "string"
    assert schema["properties"]["refund_timestamp"]["format"] == "date-time"
    assert schema["properties"]["refund_amount_cents"]["type"] == "integer"


def test_US3_AC_8_1_contract_requires_idempotency_header_without_request_body(contract):
    """TC-3.4: full-order refund input is a required header, with no body."""
    operation = refund_operation(contract)
    headers = [
        parameter for parameter in operation.get("parameters", [])
        if parameter["in"] == "header" and parameter["name"].lower() == "idempotency-key"
    ]
    assert len(headers) == 1
    assert headers[0]["required"] is True
    assert headers[0]["schema"]["type"] == "string"
    assert "requestBody" not in operation
    assert "400" in operation["responses"]


@pytest.mark.parametrize("status", ["401", "403", "404", "409", "422"])
def test_US3_AC_5_1_AC_5_2_refund_declares_protected_error_responses(contract, status):
    operation = refund_operation(contract)
    assert status in operation["responses"]
    if status != "422":
        schema = resolve_schema(
            contract, operation["responses"][status]["content"]["application/json"]["schema"]
        )
        assert set(schema["properties"]) == {"detail"}
        assert schema["properties"]["detail"]["type"] == "string"
        assert "detail" in schema["required"]


def test_US3_AC_9_4_no_get_operation_exposes_refund_audit_or_history(contract):
    """TC-3.5: inspect every GET path, including paths beyond the named examples."""
    retrieval_paths = [
        path for path, operations in contract["paths"].items()
        if "get" in operations and "refund" in path.lower()
        and ("audit" in path.lower() or "history" in path.lower())
    ]
    assert retrieval_paths == []
