import logging
from abc import ABC, abstractmethod
from typing import Any

from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class BaseRouter(ABC):
    """Базовый класс для роутеров, возвращающих строки для conditional edges."""

    @abstractmethod
    async def ainvoke(self, state: RAGState) -> str:
        """Обработка состояния и возврат строки для маршрутизации."""
        ...

    @staticmethod
    def process_input_list(message_list: list[Any]) -> list[str]:
        """Преобразует список сообщений в текстовый формат."""
        return [f"{m.type}-message: {m.content}" for m in message_list]

    @staticmethod
    def process_input_message(message: Any) -> str:
        """Преобразует сообщение в текстовый формат."""
        return f"{message.type}-message: {message.content}"


class DocsCounter(BaseRouter):
    """
    Роутер, проверяющий наличие найденных документов.
    """

    async def ainvoke(self, state: RAGState) -> str:
        """
        Проверяет, есть ли документы в state['retrieved'].

        Returns:
            'stop': если документов нет.
            'next_step': если документы есть.
        """
        if not state.get("retrieved"):
            return "stop"
        else:
            return "next_step"
