import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ECDAT Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "dev-secret-key-change-in-production-do-not-use-hardcoded"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    DATABASE_URL: str = "sqlite:///./ecdat.db"

    STORAGE_PATH: str = "./data_storage"
    SANDBOX_PATH: str = "./sandbox_storage"

    DEFAULT_QUANTUM_THREAT_HORIZON: int = 2033

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

os.makedirs(settings.STORAGE_PATH, exist_ok=True)
os.makedirs(settings.SANDBOX_PATH, exist_ok=True)
