from typing import Protocol


class FluentdConfigProtocol(Protocol):
    log_all: bool
    external_efk_enabled: bool
    external_db_enabled: bool
    app_name: str
    namespace: str
    log_level: str
    workers: int
    url: str
    verify: bool
    cert_path: str | None
    index_prefix: str
    source_type: str
    environment: str
    timeout: float
    raise_exceptions: bool
    
    @property
    def index_name(self) -> str:
        return f"{self.index_prefix}__{self.app_name}"