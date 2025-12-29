from typing import Any
from uuid import UUID


def is_valid_uuid(value: Any) -> bool:
    """
    Проверяет, является ли значение строкой в формате UUID.
    При тестовой отправке бывает шлем тестовые хедеры(test_request_1 и тд)
    """
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False
