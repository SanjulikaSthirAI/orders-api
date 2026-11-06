from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    placed = "placed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderItem(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=100)
    unit_price_cents: int = Field(ge=0)


class NewOrder(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    items: list[OrderItem] = Field(min_length=1)


class Order(BaseModel):
    id: str
    customer_name: str
    items: list[OrderItem]
    total_cents: int
    status: OrderStatus
    created_at: datetime
    delivered_at: datetime | None = None


class Error(BaseModel):
    detail: str
