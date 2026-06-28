from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://svadba:svadba@localhost:5432/svadba"

    vk_group_token: str = ""
    vk_group_id: int = 0
    vk_secret_key: str = ""
    vk_confirmation_code: str = ""

    anthropic_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_manager_id: int = 0

    yokassa_shop_id: str = ""
    yokassa_secret_key: str = ""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_base_url: str = "http://localhost:8000"

    encryption_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
