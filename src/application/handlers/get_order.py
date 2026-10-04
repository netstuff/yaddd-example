from yaddd import CrudRepository, EntityNotFoundError

from application.commands import GetOrder
from application.dto import OrderDTO
from application.registry import query_handler
from domain.order import Order


@query_handler(GetOrder)
async def get_order(query: GetOrder, orders: CrudRepository[Order]) -> OrderDTO:
    """Return an order by its identifier."""
    order = await orders.get(query.order_id)
    if order is None:
        raise EntityNotFoundError(f"Order({query.order_id}) not found")
    return OrderDTO(order_id=order.pk, total=order.total)
