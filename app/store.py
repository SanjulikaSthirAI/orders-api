"""In-memory order store with synthetic seed data. Replace with a database when this grows up."""

from collections.abc import Callable
from datetime import UTC, datetime

from app.models import NewOrder, Order, OrderItem, OrderStatus


class OrderNotFound(Exception):
    pass


class OrderNotCancellable(Exception):
    pass


def _total(items: list[OrderItem]) -> int:
    return sum(i.quantity * i.unit_price_cents for i in items)


def _seed() -> list[Order]:
    def order(n, customer, items, status, created, delivered=None):
        return Order(id=f"ORD-{n}", customer_name=customer, items=items, total_cents=_total(items), status=status,
                     created_at=datetime.fromisoformat(created), delivered_at=datetime.fromisoformat(delivered)
                     if delivered else None)

    mug = OrderItem(sku="MUG-01", name="Enamel mug", quantity=2, unit_price_cents=1250)
    lamp = OrderItem(sku="LMP-07", name="Desk lamp", quantity=1, unit_price_cents=3890)
    book = OrderItem(sku="BK-113", name="Notebook, A5", quantity=3, unit_price_cents=640)
    return [
        order(1001, "Asha Verma", [mug], OrderStatus.delivered, "2026-09-02T10:15:00+00:00",
              "2026-09-05T14:00:00+00:00"),
        order(1002, "Ben Carter", [lamp, book], OrderStatus.delivered, "2026-10-10T08:30:00+00:00",
              "2026-10-14T16:20:00+00:00"),
        order(1003, "Chen Wei", [book], OrderStatus.shipped, "2026-10-28T12:00:00+00:00"),
        order(1004, "Dara Okafor", [mug, lamp], OrderStatus.placed, "2026-11-01T09:45:00+00:00"),
        order(1005, "Elena Rossi", [book], OrderStatus.cancelled, "2026-10-20T17:10:00+00:00"),
    ]


class OrderStore:
    def __init__(self, orders: list[Order] | None = None, clock: Callable[[], datetime] = lambda: datetime.now(UTC)):
        self._orders = {o.id: o for o in (_seed() if orders is None else orders)}
        self._next = max((int(o.id.split("-")[1]) for o in self._orders.values()), default=1000) + 1
        self._clock = clock

    def list(self, status: OrderStatus | None = None) -> list[Order]:
        orders = sorted(self._orders.values(), key=lambda o: o.created_at, reverse=True)
        return [o for o in orders if status is None or o.status == status]

    def get(self, order_id: str) -> Order:
        try:
            return self._orders[order_id]
        except KeyError:
            raise OrderNotFound(order_id) from None

    def add(self, new: NewOrder) -> Order:
        order = Order(id=f"ORD-{self._next}", customer_name=new.customer_name, items=new.items,
                      total_cents=_total(new.items), status=OrderStatus.placed, created_at=self._clock())
        self._next += 1
        self._orders[order.id] = order
        return order

    def cancel(self, order_id: str) -> Order:
        order = self.get(order_id)
        if order.status != OrderStatus.placed:
            raise OrderNotCancellable(f"Order {order_id} is {order.status.value}; only placed orders can be cancelled")
        cancelled = order.model_copy(update={"status": OrderStatus.cancelled})
        self._orders[order_id] = cancelled
        return cancelled
