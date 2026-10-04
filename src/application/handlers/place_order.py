from uuid import UUID, uuid4

from yaddd import CrudRepository

from application.commands import PlaceOrder
from application.registry import command_handler
from application.transaction import Transaction
from domain.order import Order


@command_handler(PlaceOrder)
async def place_order(
    command: PlaceOrder,
    orders: CrudRepository[Order],
    tx: Transaction,
) -> UUID:
    """Create a new order and publish the corresponding domain event."""
    async with tx:
        order = Order(id=uuid4(), total=command.total)
        order.place()
        await orders.create(order)
        return order.pk
