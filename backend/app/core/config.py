from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "Pitch Platform API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "pitch_db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pitch_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/pitch_db"

    # Security & JWT
    JWT_SECRET_KEY: str = "pitch_platform_super_secret_jwt_key_development_32chars!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Settings (OpenAI / Gemini compatible)
    LLM_API_KEY: str = "dummy_llm_api_key"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-4o"

    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
