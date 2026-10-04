from uuid import UUID, uuid4

from yaddd import CrudRepository, EventPublisher

from application.commands import PlaceOrder
from application.registry import command_handler
from domain.order import Order


@command_handler(PlaceOrder)
async def place_order(
    command: PlaceOrder,
    orders: CrudRepository[Order],
    publisher: EventPublisher,
) -> UUID:
    """Create a new order and publish the corresponding domain event."""
    order = Order(id=uuid4(), total=command.total)
    order.place()
    await orders.create(order)
    await publisher.publish(order.pull_events())
    return order.pk
