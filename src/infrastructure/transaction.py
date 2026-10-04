"""Protocol-agnostic transaction implementation."""

from typing import TypeVar

from yaddd import AggregateRoot, DomainEvent, EventPublisher

from application.session import Session
from application.transaction import Transaction

T = TypeVar("T", bound=Session)


class BaseTransaction(Transaction):
    """Coordinates one or more ``Session`` resources for a single aggregate.

    On successful exit all sessions are committed and events from the tracked
    aggregate are published.  On exception all sessions are rolled back.
    Sessions are always closed on exit.
    """

    def __init__(
        self,
        sessions: list[Session],
        publisher: EventPublisher,
    ) -> None:
        self._sessions = sessions
        self._publisher = publisher
        self._aggregate: AggregateRoot | None = None

    def track(self, aggregate: AggregateRoot) -> None:
        """Register the aggregate whose events should be published on commit."""
        if self._aggregate is None:
            self._aggregate = aggregate
        elif self._aggregate is aggregate:
            return
        else:
            raise RuntimeError("Transaction can only track a single aggregate")

    def get_session(self, session_type: type[T]) -> T:
        """Return the first session of the requested concrete type."""
        for session in self._sessions:
            if isinstance(session, session_type):
                return session
        raise ValueError(f"No session of type {session_type.__name__}")

    async def __aenter__(self) -> BaseTransaction:
        for session in self._sessions:
            await session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        try:
            if exc_type is None:
                for session in self._sessions:
                    await session.commit()
                events = self._collect_events()
                await self._publisher.publish(events)
            else:
                for session in self._sessions:
                    await session.rollback()
        finally:
            for session in self._sessions:
                await session.close()

    def _collect_events(self) -> list[DomainEvent]:
        if self._aggregate is None:
            return []
        return self._aggregate.pull_events()
