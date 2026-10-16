from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(min_length=1)
    tmdb_read_token: str = Field(min_length=1)
    sync_secret: str = Field(min_length=20)
    # Encrypts each user's Stremio auth key in the database (a Fernet key)
    encryption_key: str = Field(min_length=40)
    # The web app, linked from inside Stremio (not a secret)
    ui_url: str = "https://cinematheque-categorizer.vercel.app"

    # Single-user settings from before accounts existed. Only read by
    # `python -m app.accounts import-env`, which moves them into the first
    # user's account; the app itself no longer uses them.
    addon_token: str | None = None
    api_token: str | None = None
    stremio_auth_key: str | None = None


settings = Settings()
