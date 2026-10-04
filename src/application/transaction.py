"""Application-level transactional boundary.

The ``Transaction`` protocol is an async context manager that hides the
mechanics of committing work and publishing domain events.  Handlers declare
it as a dependency and use it to mark the atomic boundary of a use case:

    async with tx:
        order = Order(...)
        order.place()
        tx.track(order)
        await orders.create(order)
        return order.pk

Tracked aggregates have their events pulled and published automatically when
the context exits successfully.  Concrete implementations live in the
infrastructure layer.
"""

from typing import Protocol

from yaddd import AggregateRoot


class Transaction(Protocol):
    """Atomic boundary for a command handler.

    Entering the context returns the transaction itself.  Exiting without
    an exception commits the work and publishes events collected from tracked
    aggregates; exiting with an exception rolls back.
    """

    def track(self, aggregate: AggregateRoot) -> None:
        """Register an aggregate whose events should be published on commit."""
        ...

    async def __aenter__(self) -> Transaction:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        ...
