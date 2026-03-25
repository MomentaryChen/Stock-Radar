from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://stockradar:stockradar@localhost:5432/stockradar"
    database_url_sync: str = "postgresql://stockradar:stockradar@localhost:5432/stockradar"
    market_data_cache_ttl_minutes: int = 30
    ticker_info_cache_ttl_hours: int = 24
    news_cache_ttl_hours: int = 6
    # Allow local dev servers (Vite may auto-pick a different port if 5173 is taken).
    cors_origins: list[str] = ["http://localhost:5173"]
    cors_origin_regex: str | None = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"
    default_benchmark: str = "0050.TW"
    risk_free_rate: float = 0.015

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
