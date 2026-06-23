from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Regionalizador API"
    debug: bool = False

    database_url: str = "sqlite:///./regionalizador.db"

    storage_dir: str = "./storage"

    awesomeapi_url: str = "https://cep.awesomeapi.com.br/json"
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    nominatim_user_agent: str = "regionalizador-app/0.1 (contato: dev@example.com)"
    geocoding_rate_limit_per_sec: float = 1.0

    cors_origins: list[str] = ["http://localhost:3000"]

    default_target_crs: str = "EPSG:31983"
    default_capacity_factor: float = 1.2


settings = Settings()
