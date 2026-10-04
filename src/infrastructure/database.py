from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

metadata = MetaData()

orders_table = Table(
    "orders",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("total", Integer, nullable=False),
)


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
