from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Global Disease Surveillance Dashboard"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://dsuser:dspass123@localhost:5432/disease_surveillance"
    SYNC_DATABASE_URL: str = "postgresql://dsuser:dspass123@localhost:5432/disease_surveillance"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # External APIs
    CDC_API_BASE: str = "https://tools.cdc.gov/api/v2/resources"
    DISEASE_SH_BASE: str = "https://disease.sh/v3/covid-19"
    WHO_GHO_BASE: str = "https://ghoapi.azureedge.net/api"
    PROMED_RSS: str = "https://promedmail.org/feed/"
    FLUVIEW_RSS: str = "https://www.cdc.gov/flu/weekly/rss.xml"
    HEALTHMAP_BASE: str = "https://healthmap.org"

    # AI Agent
    GOOGLE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    AGENT_MODEL: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
