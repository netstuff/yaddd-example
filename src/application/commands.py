from uuid import UUID

from yaddd import Command, Query


class PlaceOrder(Command):
    total: int

    def __init__(self, total: int) -> None:
        object.__setattr__(self, "total", total)


class GetOrder(Query):
    order_id: UUID

    def __init__(self, order_id: UUID) -> None:
        object.__setattr__(self, "order_id", order_id)
