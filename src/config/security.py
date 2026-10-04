from pydantic import Field
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
