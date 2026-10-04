from pydantic import Field
from pydantic_settings import BaseSettings

from config.base import AppSettings
from config.db import DatabaseSettings
from config.security import SecuritySettings


class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)


def get_settings() -> Settings:
    return Settings()
