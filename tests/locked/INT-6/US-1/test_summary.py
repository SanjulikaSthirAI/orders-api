from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Order
from app.store import OrderStore


def order(number, status, value, customer="Alice"):
    data = {"id": f"ORD-{number}", "customer_name": customer, "items": [],
            "status": status, "created_at": datetime(2026, 1, 1, tzinfo=UTC)}
    if value != "MISSING":
        data["total_cents"] = value
    return Order.model_construct(**data)


def client_for(rows):
    return TestClient(create_app(OrderStore(orders=rows)))


def expected(placed, shipped, delivered, cancelled, total):
    return {"counts": {"placed": placed, "shipped": shipped, "delivered": delivered, "cancelled": cancelled},
            "total_value_cents": total}


@pytest.mark.parametrize("rows,body", [
    ([order(1, "placed", 1000), order(2, "shipped", 2500), order(3, "delivered", 4000),
      order(4, "cancelled", 9999), order(5, "placed", 500)], expected(2, 1, 1, 1, 8000)),
])
def test_US1_AC_1_1_AC_2_2_AC_3_1_AC_3_2_summary_counts_and_total(rows, body):
    response = client_for(rows).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == body


@pytest.mark.parametrize("rows,body", [([], expected(0, 0, 0, 0, 0))])
def test_US1_AC_1_2_AC_2_1_empty_book(rows, body):
    response = client_for(rows).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == body


def test_US1_AC_1_3_list_filters_do_not_affect_global_summary():
    client = client_for([order(1, "placed", 1000), order(2, "shipped", 2000, "Bob"),
                         order(3, "cancelled", 3000)])
    filtered = client.get("/orders", params={"customer": "Alice", "status": "placed"})
    assert filtered.status_code == 200
    response = client.get("/orders/summary", params={"customer": "Alice", "status": "placed"})
    assert response.status_code == 200
    assert response.json() == expected(1, 1, 0, 1, 3000)


def test_US1_AC_2_1_absent_statuses_are_zero():
    response = client_for([order(1, "placed", 1000)]).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == expected(1, 0, 0, 0, 1000)


def test_US1_AC_2_3_AC_3_3_unknown_statuses_are_excluded():
    response = client_for([order(1, "placed", 1000), order(2, "returned", 7000),
                           order(3, "pending", 3000)]).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == expected(1, 0, 0, 0, 1000)


def test_US1_AC_3_4_missing_and_null_values_count_as_zero():
    response = client_for([order(1, "placed", None), order(2, "shipped", "MISSING"),
                           order(3, "delivered", 250)]).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == expected(1, 1, 1, 0, 250)


def test_US1_AC_3_5_negative_values_are_included():
    response = client_for([order(1, "placed", -150), order(2, "shipped", 500)]).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == expected(1, 1, 0, 0, 350)


def test_US1_AC_1_1_AC_1_2_AC_2_1_AC_3_1_summary_contract():
    contract = yaml.safe_load((Path(__file__).resolve().parents[4] / "openapi.yaml").read_text())
    schemas = contract["components"]["schemas"]
    response = contract["paths"]["/orders/summary"]["get"]["responses"]["200"]
    summary = schemas[response["content"]["application/json"]["schema"]["$ref"].split("/")[-1]]
    assert set(summary["required"]) == {"counts", "total_value_cents"}
    assert summary["properties"]["total_value_cents"]["type"] == "integer"
    counts = schemas[summary["properties"]["counts"]["$ref"].split("/")[-1]]
    assert set(counts["required"]) == {"placed", "shipped", "delivered", "cancelled"}
    assert all(counts["properties"][status]["type"] == "integer" for status in counts["required"])
