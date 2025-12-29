"""Пример схем для эндпоинта с моделями. При создании сервиса необходимо добавить нужные поля в эти модели."""

from pydantic import BaseModel


class ModelRequest(BaseModel):
    """Модель запроса к модели"""

    text: str
    temperature: float | None


class ModelResponse(BaseModel):
    """Модель ответа от модели"""

    generated_text: str
