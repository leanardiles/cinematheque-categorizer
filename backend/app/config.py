from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    tmdb_read_token: str
    addon_token: str
    sync_secret: str


settings = Settings()