from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CallGuard"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./callguard.db"
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = {"env_prefix": "CALLGUARD_", "env_file": ".env"}


settings = Settings()
