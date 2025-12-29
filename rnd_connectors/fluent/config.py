from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


class FluentdConfig(Config):
    app_name: str
    namespace: str
    log_level: str
    log_all: bool
    workers: int
    enabled: bool
    url: str
    verify: bool
    cert_path: str | None = None  # только при verify = True
    index_prefix: str
    source_type: str
    environment: str
    timeout: float
    raise_exceptions: bool
    external_db_enabled: bool
    # external_zsm_enabled: bool
    # ris_code: str
    # subsystem_code: str
    # zsm_config_item: str

    model_config = SettingsConfigDict(env_prefix="FLUENTD_")

    @property
    def index_name(self) -> str:
        return f"{self.index_prefix}__{self.app_name}"
