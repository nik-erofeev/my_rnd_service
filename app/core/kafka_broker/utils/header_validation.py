from typing import Any

from pydantic import ValidationError

from app.core.kafka_broker.schemas import HeadersTopikIn
from app.core.logger import get_logger

logger = get_logger(__name__)


class HeadersValidator:
    """Утилита для валидации заголовков Kafka сообщений"""

    # Обязательные поля для всех заголовков
    REQUIRED_FIELDS = frozenset({"requestId"})  # todo: добавить остальные

    @classmethod
    def validate_headers(
        cls,
        headers: dict[str, Any],
        strict: bool = False,
    ) -> dict[str, Any] | None:
        """
        Валидирует заголовки сообщения

        Args:
            headers: Словарь заголовков для валидации
            strict: Если True, использует строгую валидацию через Pydantic

        Returns:
            Валидированные заголовки или None при ошибке
        """
        if not headers:
            logger.warning("Заголовки отсутствуют или пусты")
            return None

        # Проверяем обязательные поля
        missing_fields = cls.REQUIRED_FIELDS - headers.keys()
        if missing_fields:
            logger.warning(f"В заголовке отсутствуют обязательные поля: {missing_fields}")
            return None

        if strict:
            # Строгая валидация через Pydantic
            return cls._validate_with_pydantic(headers)
        else:
            # Простая валидация - возвращаем как есть
            return headers

    @classmethod
    def _validate_with_pydantic(cls, headers: dict[str, Any]) -> dict[str, Any] | None:
        """Строгая валидация через Pydantic схему"""
        try:
            validated_headers = HeadersTopikIn(**headers)

            return validated_headers.model_dump()
        except ValidationError as e:
            logger.exception(f"Ошибка валидации заголовков: {e}")
            return None
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при валидации заголовков: {e}")
            return None

    @classmethod
    def get_missing_fields(cls, headers: dict[str, Any]) -> frozenset[str]:
        """Возвращает список отсутствующих обязательных полей"""
        if not headers:
            return cls.REQUIRED_FIELDS
        return cls.REQUIRED_FIELDS - headers.keys()

    @classmethod
    def create_headers(cls, request_id: str, **additional_fields: Any) -> dict[str, Any]:
        """Создает валидные заголовки с базовыми полями"""
        headers = {"requestId": request_id, **additional_fields}
        return headers


# Функции-помощники для обратной совместимости
def validate_headers(headers: dict[str, Any], strict: bool = False) -> dict[str, Any] | None:
    """Алиас для HeadersValidator.validate_headers"""
    return HeadersValidator.validate_headers(headers, strict)


def get_missing_fields(headers: dict[str, Any]) -> frozenset[str]:
    """Алиас для HeadersValidator.get_missing_fields"""
    return HeadersValidator.get_missing_fields(headers)


def create_headers(request_id: str, **additional_fields: Any) -> dict[str, Any]:
    """Алиас для HeadersValidator.create_headers"""
    return HeadersValidator.create_headers(request_id, **additional_fields)
