from typing import Any, cast

from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from yaddd_sqlalchemy import SqlCrudRepository

from domain.order import Order
from infrastructure.database import orders_table
from infrastructure.session import SqlSession
from infrastructure.transaction import BaseTransaction


class SqlOrderRepository(SqlCrudRepository[Order]):
    """Order repository bound to a transaction."""

    table = orders_table

    def __init__(self, tx: BaseTransaction) -> None:
        # The base class requires a session in __init__, but the SQLAlchemy
        # session is only available after entering the transaction context.
        # We pass a placeholder and override _session with a property that
        # reads from the active SQL session held by the transaction.
        super().__init__(cast(AsyncSession, None))
        self._tx = tx

    @property
    def _session(self) -> AsyncSession:
        sql_session = self._tx.get_session(SqlSession)
        return sql_session.session

    @_session.setter
    def _session(self, value: AsyncSession) -> None:
        pass

    async def create(self, instance: Order) -> Order:
        result = await super().create(instance)
        self._tx.track(instance)
        return result

    async def update(self, instance: Order) -> Order:
        result = await super().update(instance)
        self._tx.track(instance)
        return result

    def to_domain(self, row: Row[Any]) -> Order:
        return Order(id=row.id, total=row.total)

    def to_row(self, instance: Order) -> dict[str, Any]:
        return {"id": instance.pk, "total": instance.total}
