from shared.config import BaseConfig


class Settings(BaseConfig):
    github_token: str = ""
    tmdb_api_key: str = ""
    rawg_api_key: str = ""
    lastfm_api_key: str = ""

    item_ttl_days: int = 7


settings = Settings()
