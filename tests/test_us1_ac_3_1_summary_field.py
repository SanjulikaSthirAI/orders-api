from fastapi.testclient import TestClient

from app.main import create_app
from app.store import OrderStore


def test_us1_ac_3_1_summary_exposes_non_cancelled_total_in_cents():
    app = create_app(OrderStore())
    response = TestClient(app).get("/orders/summary")
    assert response.status_code == 200
    assert response.json() == {
        "counts": {"placed": 1, "shipped": 1, "delivered": 2, "cancelled": 1},
        "non_cancelled_total_value_cents": 16620,
    }
    schema = app.openapi()["components"]["schemas"]["OrderSummary"]
    assert "non_cancelled_total_value_cents" in schema["required"]
    assert schema["properties"]["non_cancelled_total_value_cents"]["type"] == "integer"
