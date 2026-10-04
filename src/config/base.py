from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    name: str = Field(default="yaddd-example", alias="APP_NAME")
    debug: bool = Field(default=False, alias="APP_DEBUG")
