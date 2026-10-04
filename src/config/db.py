from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    dsn: str = Field(
        default="postgresql+asyncpg://postgres:pass@localhost:5432/yaddd_example",
        alias="DATABASE_URL",
    )
