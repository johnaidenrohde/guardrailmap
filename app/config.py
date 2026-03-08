from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'GuardrailMap'
    secret_key: str = 'change-me'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24

    database_url: str = 'sqlite:///./guardrailmap.db'

    spaces_endpoint_url: str | None = None
    spaces_region: str = 'nyc3'
    spaces_bucket: str | None = None
    spaces_key: str | None = None
    spaces_secret: str | None = None
    spaces_public_base_url: str | None = None

    mapillary_access_token: str | None = None


settings = Settings()
