"""In-process command and query buses.

Each dispatch opens a fresh SQLAlchemy session, builds the requested handler
through a pre-registered factory, and executes it.  The bus itself is agnostic
to whether the handler is a class or a function; the composition root supplies
a factory that returns a callable of the form ``handler(command) -> result``.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from yaddd import Command, EventPublisher, Query

_CommandFactory = Callable[[AsyncSession], Callable[[Command], Any]]
_QueryFactory = Callable[[AsyncSession], Callable[[Query], Any]]


class CommandBus:
    """Dispatches commands to their registered handlers."""

    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        publisher: EventPublisher,
    ) -> None:
        self._session_maker = session_maker
        self._publisher = publisher
        self._handlers: dict[type[Command], _CommandFactory] = {}

    def register(
        self,
        command_type: type[Command],
        factory: _CommandFactory,
    ) -> None:
        """Register a handler factory for a command type."""
        self._handlers[command_type] = factory

    async def dispatch(self, command: Command) -> Any:
        """Execute the handler for the given command and commit the session."""
        factory = self._handlers[type(command)]
        async with self._session_maker() as session:
            handler = factory(session)
            result = await handler(command)
            await session.commit()
            return result


class QueryBus:
    """Dispatches queries to their registered handlers."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker
        self._handlers: dict[type[Query], _QueryFactory] = {}

    def register(
        self,
        query_type: type[Query],
        factory: _QueryFactory,
    ) -> None:
        """Register a handler factory for a query type."""
        self._handlers[query_type] = factory

    async def dispatch(self, query: Query) -> Any:
        """Execute the handler for the given query."""
        factory = self._handlers[type(query)]
        async with self._session_maker() as session:
            handler = factory(session)
            return await handler(query)
