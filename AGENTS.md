# Orders API: guide for coding agents

Synthetic demo service. Its data is made up and lives in memory.

## Layout

- `app/main.py`: FastAPI routes. `create_app(store)` builds the app; tests pass their own store.
- `app/models.py`: Pydantic request and response models.
- `app/store.py`: the in-memory `OrderStore` and its seed data.
- `openapi.yaml`: the published API contract, generated from the app (see below).
- `tests/`: pytest. One test file per concern; the contract test compares `openapi.yaml` to the app.

## Commands

- Install: `pip install -r requirements-dev.txt`
- Lint: `ruff check .`
- Test: `pytest -q`
- Run locally: `uvicorn app.main:app --reload` (port 8000)
- Regenerate the contract after any API change: `python scripts/export_openapi.py`

## Rules

- Keep `openapi.yaml` and the app in step. A change to a route, model or status code is a contract change:
  regenerate the file in the same commit.
- Money is an integer number of cents (`*_cents`). Never use floats.
- Errors are `{"detail": "<message>"}` with the right status: 404 unknown id, 409 state conflict, 422 bad input.
- Every new behaviour needs a test that names the case it covers. Cover the failure paths, not only the happy one.
- Do not edit `.github/`, `AGENTS.md` or `openapi.yaml` by hand outside a contract change; they are code-owned.

<!-- protected-contracts:start INT-2 -->
## Protected contracts (INT-2)

Stories must not change these unless plan.json marks the story as a contract change.

- File: `app/main.py`
- File: `app/models.py`
- File: `app/store.py`
- File: `openapi.yaml`
- Endpoint: `GET /orders`
- Endpoint: `GET /orders/{order_id}`
- Endpoint: `POST /orders`
- Endpoint: `POST /orders/{order_id}/cancel`
- Endpoint: `POST /orders/{order_id}/refunds`
<!-- protected-contracts:end INT-2 -->
