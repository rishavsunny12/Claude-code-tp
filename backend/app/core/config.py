from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://harvestguard:secret@localhost:5432/harvestguard"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Anthropic
    anthropic_api_key: str = ""

    # NASA Earthdata (free at urs.earthaccess.nasa.gov)
    earthdata_username: str = ""
    earthdata_password: str = ""

    # App
    app_name: str = "HarvestGuard"
    debug: bool = False

    # Rate limiting
    rate_limit_forecast: str = "10/minute"
    rate_limit_chat: str = "20/minute"

    # Data refresh cache TTL in seconds
    hunger_map_cache_ttl: int = 21600   # 6 hours
    ndvi_cache_ttl: int = 1382400       # 16 days
    chirps_cache_ttl: int = 86400       # 1 day


@lru_cache
def get_settings() -> Settings:
    return Settings()
