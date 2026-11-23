from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://evalforge:evalforge@localhost:5432/evalforge"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]
    openai_api_key: str = ""
    anthropic_api_key: str = ""


settings = Settings()
