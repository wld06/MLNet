from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/mlnest"
    REDIS_URL: str = "redis://localhost:6379/0"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "mlnest-datasets"

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    SECRET_KEY: str = "cambia-esto-en-produccion"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    MAX_DATASET_SIZE_MB: int = 500
    CLEANING_PREVIEW_ROWS: int = 1000
    CLEANING_CACHE_TTL: int = 3600


settings = Settings()
