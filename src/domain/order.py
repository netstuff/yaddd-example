from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from yaddd import AggregateRoot, BusinessRule, DomainEvent


class PositiveTotal(BusinessRule["Order"]):
    message = "total must be positive"

    def is_satisfied_by(self, candidate: Order) -> bool:
        return candidate.total > 0


class OrderPlaced(DomainEvent):
    order_id: UUID

    def __init__(self, order_id: UUID) -> None:
        object.__setattr__(self, "order_id", order_id)
        object.__setattr__(self, "occurred_at", datetime.now(UTC))


@dataclass(eq=False, kw_only=True)
class Order(AggregateRoot):
    id: UUID
    total: int

    INVARIANTS = (PositiveTotal(),)

    @property
    def pk(self) -> UUID:
        return self.id

    def place(self) -> None:
        self.add_event(OrderPlaced(order_id=self.pk))
