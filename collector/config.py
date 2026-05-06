from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "intel"
    db_user: str = "intel"
    db_password: str = "changeme"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma2:2b"

    github_token: str = ""
    tmdb_api_key: str = ""
    rawg_api_key: str = ""
    lastfm_api_key: str = ""

    log_level: str = "INFO"

    @property
    def db_dsn(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
