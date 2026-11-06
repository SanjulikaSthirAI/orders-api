"""The committed openapi.yaml is the API contract. Change the API and the file together:
`python scripts/export_openapi.py`, then review the diff."""

from pathlib import Path

import yaml

from app.main import app

CONTRACT = Path(__file__).resolve().parent.parent / "openapi.yaml"


def test_openapi_yaml_matches_the_app():
    committed = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert committed == app.openapi(), "openapi.yaml is out of date; run python scripts/export_openapi.py"


def test_the_contract_lists_the_published_operations():
    paths = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))["paths"]
    operations = {f"{method.upper()} {path}" for path, ops in paths.items() for method in ops}
    assert operations == {"GET /orders", "POST /orders", "GET /orders/{order_id}", "POST /orders/{order_id}/cancel",
                          "POST /orders/{order_id}/refunds"}
