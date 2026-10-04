from uuid import UUID

from yaddd import DTO


class OrderDTO(DTO):
    order_id: UUID
    total: int

    def __init__(self, order_id: UUID, total: int) -> None:
        object.__setattr__(self, "order_id", order_id)
        object.__setattr__(self, "total", total)
