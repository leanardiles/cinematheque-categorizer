from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(min_length=1)
    tmdb_read_token: str = Field(min_length=1)
    addon_token: str = Field(min_length=20)
    api_token: str = Field(min_length=20)
    sync_secret: str = Field(min_length=20)
    stremio_auth_key: str = Field(min_length=10)


settings = Settings()