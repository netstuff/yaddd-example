from typing import Any

from sqlalchemy.engine import Row
from yaddd_sqlalchemy import SqlCrudRepository

from domain.order import Order
from infrastructure.database import orders_table


class SqlOrderRepository(SqlCrudRepository[Order]):
    table = orders_table

    def to_domain(self, row: Row[Any]) -> Order:
        return Order(id=row.id, total=row.total)

    def to_row(self, instance: Order) -> dict[str, Any]:
        return {"id": instance.pk, "total": instance.total}
