"""Regenerate openapi.yaml from the app. `tests/test_contract.py` fails when the two disagree.

    python scripts/export_openapi.py
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

(ROOT / "openapi.yaml").write_text(yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True), encoding="utf-8")
print("wrote openapi.yaml")
