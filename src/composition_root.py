"""Composition root: wires together infrastructure, application and domain layers.

This is the single place where concrete implementations are chosen and
connected. It owns the SQLAlchemy engine, wires the in-memory domain event
publisher, and registers command/query handlers that were populated via the
`@command_handler` / `@query_handler` decorators.

`init_db()` is called once at startup to create missing tables;
`dispose()` is called on shutdown to release the async engine.
"""

import inspect
from collections.abc import Callable
from typing import Any, get_args, get_origin

from yaddd import (
    CrudRepository,
    DomainEvent,
    InMemoryEventPublisher,
)

# Importing the handlers package runs the decorators and populates the
# module-level registry.  This is the only place where the application
# layer is touched during wiring.
from application import handlers  # noqa: F401
from application.registry import registry
from application.transaction import Transaction
from config import Settings, get_settings
from domain.order import Order, OrderPlaced
from infrastructure.bus import CommandBus, QueryBus
from infrastructure.database import (
    create_engine,
    create_session_maker,
    metadata,
)
from infrastructure.repositories import SqlOrderRepository
from infrastructure.session import SqlSession
from infrastructure.transaction import BaseTransaction


class CompositionRoot:
    """Wires all layers and exposes the command/query buses."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.engine = create_engine(self.settings.db.dsn)
        self.session_maker = create_session_maker(self.engine)
        self.publisher = InMemoryEventPublisher()
        self.publisher.subscribe(OrderPlaced, self._on_order_placed)

        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all handlers collected by the decorators."""
        for command_type, handler in registry.commands.items():
            self.command_bus.register(
                command_type,
                self._build_handler(handler),
            )

        for query_type, handler in registry.queries.items():
            self.query_bus.register(
                query_type,
                self._build_handler(handler),
            )

    def _build_handler(
        self,
        handler: Callable[..., Any] | type[Any],
    ) -> Callable[[Any], Any]:
        """Build a callable handler with all dependencies resolved."""
        if inspect.isclass(handler):
            return self._build_class_handler(handler)
        return self._build_function_handler(handler)

    def _build_class_handler(
        self,
        handler_class: type[Any],
    ) -> Callable[[Any], Any]:
        def invoke(message: Any) -> Any:
            tx = self._create_transaction()
            init_signature = inspect.signature(handler_class.__init__)
            params = list(init_signature.parameters.values())[1:]  # skip self
            deps = [self._resolve_dependency(param.annotation, tx) for param in params]
            instance = handler_class(*deps)
            return instance.handle(message)

        return invoke

    def _build_function_handler(
        self,
        func: Callable[..., Any],
    ) -> Callable[[Any], Any]:
        def invoke(message: Any) -> Any:
            tx = self._create_transaction()
            signature = inspect.signature(func)
            params = list(signature.parameters.values())
            dep_params = params[1:]  # first parameter is the command/query
            deps = [self._resolve_dependency(param.annotation, tx) for param in dep_params]
            return func(message, *deps)

        return invoke

    def _create_transaction(self) -> BaseTransaction:
        """Create a transaction with a SQLAlchemy session."""
        sql_session = SqlSession(self.session_maker)
        return BaseTransaction([sql_session], self.publisher)

    def _resolve_dependency(self, annotation: Any, tx: BaseTransaction) -> Any:
        """Resolve a constructor/function parameter to a concrete dependency."""
        if annotation is Transaction:
            return tx

        origin = get_origin(annotation)
        if origin is CrudRepository:
            (entity_type,) = get_args(annotation)
            if entity_type is Order:
                return SqlOrderRepository(tx)

        raise ValueError(f"Unsupported dependency type: {annotation}")

    async def init_db(self) -> None:
        """Create any missing database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def dispose(self) -> None:
        """Release the SQLAlchemy engine."""
        await self.engine.dispose()

    @staticmethod
    async def _on_order_placed(event: DomainEvent) -> None:
        if isinstance(event, OrderPlaced):
            print(f"[event] OrderPlaced: {event.order_id}")
