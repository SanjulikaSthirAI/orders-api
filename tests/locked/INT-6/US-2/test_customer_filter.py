from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Order
from app.store import OrderStore


def order(number, customer, status):
    data = {"id": f"ORD-{number}", "items": [], "total_cents": 100, "status": status,
            "created_at": datetime(2026, 1, 1, tzinfo=UTC)}
    if customer != "MISSING":
        data["customer_name"] = customer
    return Order.model_construct(**data)


def check(rows, params, ids):
    client = TestClient(create_app(OrderStore(orders=rows)))
    response = client.get("/orders", params=params)
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == set(ids)


def test_US2_AC_4_1_exact_customer_filter():
    check([order(1, "Alice", "placed"), order(2, "Bob", "placed"), order(3, "Alice", "shipped")],
          {"customer": "Alice"}, ["ORD-1", "ORD-3"])


def test_US2_AC_4_2_customer_filter_is_trimmed():
    check([order(1, "Alice", "placed"), order(2, "Bob", "placed")], {"customer": " Alice "}, ["ORD-1"])


def test_US2_AC_4_3_customer_filter_is_case_sensitive():
    check([order(1, "Alice", "placed")], {"customer": "alice"}, [])


def test_US2_AC_4_4_nonmatching_customer_returns_empty_list():
    check([order(1, "Alice", "placed")], {"customer": "Charlie"}, [])


def test_US2_AC_4_5_missing_and_null_customers_do_not_match():
    check([order(1, None, "placed"), order(2, "MISSING", "shipped"), order(3, "Alice", "delivered")],
          {"customer": "Alice"}, ["ORD-3"])


@pytest.mark.parametrize("customer", ["", "   "])
def test_US2_AC_4_7_blank_customer_does_not_filter(customer):
    check([order(1, "Alice", "placed"), order(2, "Bob", "shipped")],
          {"customer": customer}, ["ORD-1", "ORD-2"])


def test_US2_AC_5_1_customer_and_status_both_match():
    check([order(1, "Alice", "placed"), order(2, "Alice", "shipped"), order(3, "Bob", "placed")],
          {"customer": " Alice ", "status": "placed"}, ["ORD-1"])


def test_US2_AC_5_2_status_only():
    check([order(1, "Alice", "placed"), order(2, "Bob", "placed"), order(3, "Alice", "shipped")],
          {"status": "placed"}, ["ORD-1", "ORD-2"])


def test_US2_AC_5_3_absent_customer_does_not_filter():
    check([order(1, "Alice", "placed"), order(2, "Bob", "shipped")], {}, ["ORD-1", "ORD-2"])


def test_US2_AC_4_1_AC_5_1_AC_5_2_AC_5_3_customer_filter_contract():
    contract = yaml.safe_load((Path(__file__).resolve().parents[4] / "openapi.yaml").read_text())
    operation = contract["paths"]["/orders"]["get"]
    params = {p["name"]: p for p in operation["parameters"] if p["in"] == "query"}
    assert params["customer"]["required"] is False
    assert params["status"]["required"] is False
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "array"
    assert schema["items"]["$ref"] == "#/components/schemas/Order"
