from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


class TokenManagerConfig(Config):
    login: str
    password: str
    url: str
    verify: bool = False

    model_config = SettingsConfigDict(env_prefix="YATOKEN_")


class YandexEmbeddingConfig(Config):
    api_url: str
    model: str
    folder_id: str
    use_ssl: bool = False

    model_config = SettingsConfigDict(env_prefix="EMBEDDER_")


class YandexGPTLLMConfig(Config):
    api_url: str
    model: str
    folder_id: str
    temperature: float
    max_tokens: int
    use_ssl: bool = False
    stream: bool = False
    reasoning_mode: str | None = None
    
    model_config = SettingsConfigDict(env_prefix="YAGPT_")
