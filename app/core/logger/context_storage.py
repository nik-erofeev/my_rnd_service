from contextvars import ContextVar
from typing import Any, Generic, TypeVar

from rnd_connectors.fluent.schemas import StagesKafkaMessages

T = TypeVar("T")


class ContextStorage(Generic[T]):
    """Безопасное хранилище на ContextVar без Token."""

    def __init__(self, name: str, default: T):
        self._default = default
        self._var = ContextVar(name, default=default)

    def get(self) -> T:
        return self._var.get()

    def set(self, value: T) -> None:
        self._var.set(value)

    def reset(self) -> None:
        self._var.set(self._default)


# Контекстное хранилище для request_id
request_id = ContextStorage[str]("requestId", "-")

# Контекстное хранилище для stages
stages_context = ContextStorage[StagesKafkaMessages](
    "stages",
    StagesKafkaMessages(),
)

# Контекст для headers текущего сообщения
message_headers = ContextStorage[dict[str, Any]]("headers", {})

# Контекст для key текущего сообщения
message_key = ContextStorage[bytes | None]("key", None)


def reset_request_context() -> None:
    """Сбрасывает все контекстные переменные (для middleware)."""
    request_id.reset()
    stages_context.reset()
    message_headers.reset()
    message_key.reset()
