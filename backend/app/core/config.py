"""
Application configuration for PRAMAAN Backend.

Loads environment variables via Pydantic Settings.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Environment
    ENVIRONMENT: str = Field(default="development", description="development, staging, or production")
    DEBUG: bool = Field(default=False)
    PROJECT_NAME: str = Field(default="PRAMAAN Core Backend")
    VERSION: str = Field(default="0.1.0")
    API_V1_PREFIX: str = Field(default="/api/v1")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)

    # Security & CORS
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
        description="Allowed origins for CORS",
    )
    SECRET_KEY: str = Field(default="insecure-dev-key-change-in-production")

    # Persistence Configuration
    DATABASE_URL: str = Field(default="sqlite:///:memory:", description="PostgreSQL or SQLite connection URI")
    TEST_DATABASE_URL: str = Field(default="sqlite:///:memory:")

    # Asynchronous Infrastructure (Optional in Phase 0)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    S3_ENDPOINT_URL: str = Field(default="http://localhost:9000")
    S3_ACCESS_KEY: str = Field(default="pramaan_minio_admin")
    S3_SECRET_KEY: str = Field(default="pramaan_minio_password")
    S3_BUCKET_NAME: str = Field(default="pramaan-evidence-assets")
    S3_REGION: str = Field(default="us-east-1")
    STORAGE_BASE_DIR: str = Field(default="./storage")

    # Upload Limits & Performance
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=524_288_000, description="Max upload size (500 MB)")
    LOG_LEVEL: str = Field(default="INFO")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()

