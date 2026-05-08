from shared.config import BaseConfig


class Settings(BaseConfig):
    telegram_token: str
    telegram_allowed_user_id: int = 0  # 0 = sin restricción


settings = Settings()
