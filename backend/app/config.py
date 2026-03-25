from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://stockradar:stockradar@localhost:5432/stockradar"
    database_url_sync: str = "postgresql://stockradar:stockradar@localhost:5432/stockradar"
    market_data_cache_ttl_minutes: int = 30
    ticker_info_cache_ttl_hours: int = 24
    cors_origins: list[str] = ["http://localhost:5173"]
    default_benchmark: str = "0050.TW"
    risk_free_rate: float = 0.015

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
