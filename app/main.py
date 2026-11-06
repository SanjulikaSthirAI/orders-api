import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import Error, NewOrder, Order, OrderStatus
from app.store import OrderNotCancellable, OrderNotFound, OrderStore

# The browser UI's origins. Override with ORDERS_UI_ORIGINS (comma-separated) outside local development.
DEFAULT_UI_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"

NOT_FOUND = {404: {"model": Error, "description": "No such order"}}


def create_app(store: OrderStore | None = None) -> FastAPI:
    app = FastAPI(title="Orders API", version="1.0.0", description="Orders for the demo shop.")
    origins = os.environ.get("ORDERS_UI_ORIGINS", DEFAULT_UI_ORIGINS).split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])
    orders = store if store is not None else OrderStore()

    @app.get("/orders", response_model=list[Order], summary="List orders, newest first")
    def list_orders(status: OrderStatus | None = None) -> list[Order]:
        return orders.list(status)

    @app.get("/orders/{order_id}", response_model=Order, responses=NOT_FOUND, summary="Get one order")
    def get_order(order_id: str) -> Order:
        try:
            return orders.get(order_id)
        except OrderNotFound:
            raise HTTPException(404, f"Order {order_id} not found") from None

    @app.post("/orders", response_model=Order, status_code=201, summary="Place an order")
    def place_order(new: NewOrder) -> Order:
        return orders.add(new)

    @app.post("/orders/{order_id}/cancel", response_model=Order,
              responses={**NOT_FOUND, 409: {"model": Error, "description": "The order is no longer cancellable"}},
              summary="Cancel an order that has not shipped")
    def cancel_order(order_id: str) -> Order:
        try:
            return orders.cancel(order_id)
        except OrderNotFound:
            raise HTTPException(404, f"Order {order_id} not found") from None
        except OrderNotCancellable as e:
            raise HTTPException(409, str(e)) from None

    return app


app = create_app()
