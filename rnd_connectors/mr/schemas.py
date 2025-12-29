from pydantic_settings import BaseSettings
from typing import NamedTuple


class MRConfig(BaseSettings):
    """Конфигурация для подключения к  Model Repo."""

    email: str
    password: str
    rest_base_url_mr: str = "https://mr-model-registry-service.pim-ss.region.vtb.ru"
    batch_size : int = 2

    class ConfigDict:
        env_prefix = "MODEL_REPO_"

class DownloadBatchResult(NamedTuple):
    """Результат скачивания батча файлов."""

    results: list
    success: bool
