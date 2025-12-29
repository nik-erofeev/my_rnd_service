from typing import Protocol


class TokenManagerConfigProtocol(Protocol):
    login: str
    password: str
    url: str
    verify: bool


class YandexEmbeddingConfigProtocol(Protocol):
    api_url: str
    folder_id: str
    model: str
    use_ssl: bool


class YandexGPTLLMConfigProtocol(Protocol):
    api_url: str
    model: str
    folder_id: str
    temperature: float
    max_tokens: int
    use_ssl: bool
    stream: bool
    reasoning_mode: str | None
