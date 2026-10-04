"""Composition root: wires together infrastructure, application and domain layers.

This is the single place where concrete implementations are chosen and
connected. It owns the SQLAlchemy engine, builds per-request sessions,
exposes the CRUD repository, wires the in-memory domain event publisher,
and registers command/query handlers that were populated via the
`@command_handler` / `@query_handler` decorators.

`init_db()` is called once at startup to create missing tables;
`dispose()` is called on shutdown to release the async engine.
"""

import inspect
from collections.abc import Callable
from typing import Any, get_args, get_origin

from sqlalchemy.ext.asyncio import AsyncSession
from yaddd import (
    CrudRepository,
    DomainEvent,
    EventPublisher,
    InMemoryEventPublisher,
)

# Importing the handlers package runs the decorators and populates the
# module-level registry.  This is the only place where the application
# layer is touched during wiring.
from application import handlers  # noqa: F401
from application.registry import registry
from config import Settings, get_settings
from domain.order import Order, OrderPlaced
from infrastructure.bus import CommandBus, QueryBus
from infrastructure.database import (
    create_engine,
    create_session_maker,
    metadata,
)
from infrastructure.repositories import SqlOrderRepository


class CompositionRoot:
    """Wires all layers and exposes the command/query buses."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.engine = create_engine(self.settings.db.dsn)
        self.session_maker = create_session_maker(self.engine)
        self.publisher = InMemoryEventPublisher()
        self.publisher.subscribe(OrderPlaced, self._on_order_placed)

        self.command_bus = CommandBus(self.session_maker, self.publisher)
        self.query_bus = QueryBus(self.session_maker)
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all handlers collected by the decorators."""
        for command_type, handler in registry.commands.items():
            self.command_bus.register(
                command_type,
                self._build_handler_factory(handler),
            )

        for query_type, handler in registry.queries.items():
            self.query_bus.register(
                query_type,
                self._build_handler_factory(handler),
            )

    def _build_handler_factory(
        self,
        handler: Callable[..., Any] | type[Any],
    ) -> Callable[[AsyncSession], Callable[[Any], Any]]:
        """Build a session-bound factory for a class or function handler."""
        if inspect.isclass(handler):
            return self._build_class_factory(handler)
        return self._build_function_factory(handler)

    def _build_class_factory(
        self,
        handler_class: type[Any],
    ) -> Callable[[AsyncSession], Callable[[Any], Any]]:
        def factory(session: AsyncSession) -> Callable[[Any], Any]:
            init_signature = inspect.signature(handler_class.__init__)
            params = list(init_signature.parameters.values())[1:]  # skip self
            deps = [self._resolve_dependency(session, param.annotation) for param in params]
            instance = handler_class(*deps)
            return lambda message: instance.handle(message)

        return factory

    def _build_function_factory(
        self,
        func: Callable[..., Any],
    ) -> Callable[[AsyncSession], Callable[[Any], Any]]:
        def factory(session: AsyncSession) -> Callable[[Any], Any]:
            signature = inspect.signature(func)
            params = list(signature.parameters.values())
            dep_params = params[1:]  # first parameter is the command/query
            deps = [self._resolve_dependency(session, param.annotation) for param in dep_params]
            return lambda message: func(message, *deps)

        return factory

    def _resolve_dependency(self, session: AsyncSession, annotation: Any) -> Any:
        """Resolve a constructor/function parameter to a concrete dependency."""
        if annotation is EventPublisher:
            return self.publisher

        origin = get_origin(annotation)
        if origin is CrudRepository:
            (entity_type,) = get_args(annotation)
            if entity_type is Order:
                return self.order_repository(session)

        raise ValueError(f"Unsupported dependency type: {annotation}")

    async def init_db(self) -> None:
        """Create any missing database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def dispose(self) -> None:
        """Release the SQLAlchemy engine."""
        await self.engine.dispose()

    def order_repository(self, session: AsyncSession) -> SqlOrderRepository:
        """Build an order repository bound to the given session."""
        return SqlOrderRepository(session)

    @staticmethod
    async def _on_order_placed(event: DomainEvent) -> None:
        if isinstance(event, OrderPlaced):
            print(f"[event] OrderPlaced: {event.order_id}")
