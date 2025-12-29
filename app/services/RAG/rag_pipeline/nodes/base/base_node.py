import logging
from abc import ABC, abstractmethod

from langchain_core.messages import BaseMessage

from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class EntryNode(ABC):
    """Базовый класс для всех узлов обработки в графе RAG.

    Каждый узел должен реализовать метод invoke для обработки состояния.
    """

    @abstractmethod
    async def ainvoke(self, state: RAGState) -> RAGState:
        """Обработка состояния узлом.

        Args:
            state: Входное состояние с сообщениями и данными

        Returns:
            Обновленное состояние после обработки
        """
        return {
            "messages": state["messages"],
            "retrieved": state["retrieved"],
            "intent": state["intent"],
        }


class BaseNode(EntryNode):
    """Базовый класс узла с общими методами обработки сообщений."""

    async def ainvoke(self, state: RAGState) -> RAGState:
        """Реализация обработки состояния."""
        return {
            "messages": state["messages"],
            "retrieved": state["retrieved"],
            "intent": state["intent"],
        }

    @staticmethod
    def process_input_list(message_list: list[BaseMessage]) -> list[str]:
        """Преобразует список сообщений в текстовый формат.

        Args:
            message_list: Список сообщений для обработки

        Returns:
            Список строк в формате "тип-message: содержимое"
        """
        return [f"{m.type}-message: {m.content}" for m in message_list]

    @staticmethod
    def process_input_message(message: BaseMessage) -> str:
        """Преобразует сообщение в текстовый формат.

        Args:
            message: Сообщение для обработки

        Returns:
            Строка в формате "тип-message: содержимое"
        """
        return f"{message.type}-message: {message.content}"
