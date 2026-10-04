"""In-process command and query buses.

The buses are pure routers: they receive a message, look up the registered
handler, and invoke it.  Persistence and transaction handling are delegated
to the handlers and the ``Transaction`` context manager supplied by the
composition root.
"""

from collections.abc import Callable
from typing import Any

from yaddd import Command, Query

_CommandHandler = Callable[[Command], Any]
_QueryHandler = Callable[[Query], Any]


class CommandBus:
    """Dispatches commands to their registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Command], _CommandHandler] = {}

    def register(
        self,
        command_type: type[Command],
        handler: _CommandHandler,
    ) -> None:
        """Register a handler for a command type."""
        self._handlers[command_type] = handler

    async def dispatch(self, command: Command) -> Any:
        """Execute the handler for the given command."""
        handler = self._handlers[type(command)]
        return await handler(command)


class QueryBus:
    """Dispatches queries to their registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Query], _QueryHandler] = {}

    def register(
        self,
        query_type: type[Query],
        handler: _QueryHandler,
    ) -> None:
        """Register a handler for a query type."""
        self._handlers[query_type] = handler

    async def dispatch(self, query: Query) -> Any:
        """Execute the handler for the given query."""
        handler = self._handlers[type(query)]
        return await handler(query)
