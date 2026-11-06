# orders-api

A small orders service for the SDLC orchestrator demo. Data is synthetic and in memory.

| Method | Path | Does |
| --- | --- | --- |
| GET | `/orders?status=` | List orders, newest first; optional status filter |
| GET | `/orders/{order_id}` | One order |
| POST | `/orders` | Place an order (total is computed from the items) |
| POST | `/orders/{order_id}/cancel` | Cancel an order that is still `placed` |

Statuses: `placed`, `shipped`, `delivered`, `cancelled`. There is no refund or return flow yet.

## Run

```sh
pip install -r requirements-dev.txt
uvicorn app.main:app --reload      # http://localhost:8000/docs
pytest -q
ruff check .
```

`openapi.yaml` is the contract. After changing the API: `python scripts/export_openapi.py`.
