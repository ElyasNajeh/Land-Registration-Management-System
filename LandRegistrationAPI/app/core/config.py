from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Land Registration API"
    API_PREFIX: str = "/api"
    DATABASE_NAME: str = "land_registration"
    MONGODB_URL: str = "mongodb://127.0.0.1:27017"
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173"
    STAFF_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", "LandRegistrationAPI/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
