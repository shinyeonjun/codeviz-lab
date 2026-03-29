from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CodeViz Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = "postgresql+psycopg://codeviz:codeviz@127.0.0.1:55433/codeviz"
    runner_backend: str = "docker"
    runner_timeout_seconds: int = 5
    runner_docker_image: str = "codeviz-python-sandbox:latest"
    runner_docker_memory_limit: str = "256m"
    runner_docker_cpus: str = "0.5"
    runner_docker_pids_limit: int = 64
    runner_docker_tmpfs_size: str = "64m"
    runner_max_trace_steps: int = 500
    runner_max_stdout_chars: int = 10000
    runner_max_source_code_chars: int = 20000
    runner_max_stdin_chars: int = 4000
    visualization_selector_backend: str = "manual"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    openai_api_url: str = "https://api.openai.com/v1/responses"
    openai_timeout_seconds: int = 8
    openai_max_output_tokens: int = 600
    openai_reasoning_effort: str = "low"
    openai_text_verbosity: str = "low"
    openai_project_id: str | None = None
    openai_organization_id: str | None = None
    auth_cookie_name: str = "codeviz_session"
    auth_session_ttl_days: int = 30
    auth_cookie_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql+psycopg://", "postgresql://")):
            raise ValueError("DATABASE_URL은 PostgreSQL 연결 문자열이어야 합니다.")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
