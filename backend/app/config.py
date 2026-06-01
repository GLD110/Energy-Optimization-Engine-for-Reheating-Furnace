from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Reheating Furnace Energy API"
    database_url: str = "sqlite+aiosqlite:///./furnace.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ml_artifact_path: str = "ml/artifacts/lstm_curve.pt"
    num_zones: int = 5
    sequence_length: int = 48


settings = Settings()
