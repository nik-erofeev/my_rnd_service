from __future__ import annotations

import logging
from typing import Any

from ___check.langfuse import handler
from app.core.kafka_broker.schemas import (
    ERROR_TRACES,
    CodeError,
    ErrorInfo,
    LangchainConsumerMessage,
    LangchainProducerMessage,
    StatusCode,
)
from app.services.RAG.rag_pipeline.pipeline import RAGPipeline
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


def _extract_question(inputs: dict) -> dict:
    """
    Функция-фильтр. Она принимает все аргументы вашей функции (body, headers, key)
    """
    # Достаем сам вопрос.
    # inputs["body"] - это объект LangchainConsumerMessage
    # LangSmith превращает Pydantic модели в dict, поэтому обращаемся по ключу
    try:
        # Если body уже словарь
        question = inputs["body"].get("test_questions", "No question")
    except AttributeError:
        # Если body все еще объект Pydantic (иногда бывает)
        question = inputs["body"].test_questions

    # Возвращаем то, что хотим видеть в Input в LangSmith
    # Можно вернуть строку или словарь
    return {"question": question}


class RagService:
    """Сервис, использующий RAG-пайплайн (LangChain адаптер)."""

    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    # from langsmith import traceable

    # @traceable(run_type="chain", name="Handle Kafka Message")
    # @traceable(run_type="chain", name="Handle Kafka Message", process_inputs=_extract_question)
    async def handle_message(
        self,
        body: LangchainConsumerMessage,
        headers: dict[str, Any],
        key: bytes | None = None,
    ) -> LangchainProducerMessage:
        """
        Обрабатывает входящее сообщение через LangChain граф.
        """
        logger.info("Начало обработки сообщения через LangChain RAG")

        state: RAGState = await self.pipeline.query(
            body.test_questions,
            callbacks=[handler],
        )

        # Извлечение ответа из state
        messages = state.get("messages", [])
        answer = "Нет ответа"
        if messages:
            content = messages[-1].content
            # Берем последнее сообщение (обычно это ответ AI)
            answer = content if isinstance(content, str) else str(content)

        logger.info(f"Получен ответ RAG: {answer[:100]}...")
        return LangchainProducerMessage(message=answer, statusCode=StatusCode.SUCCESS)

    @classmethod
    def create_error_message(
        cls,
        status_code: StatusCode,
        code_error: CodeError,
        error_message: str | None = None,
    ) -> LangchainProducerMessage:
        """
        Формирует сообщение об ошибке для отправки в Kafka.
        """

        return LangchainProducerMessage(
            message="ошибка",
            statusCode=status_code,
            errorInfo=[
                ErrorInfo(
                    codeError=code_error,
                    trace=ERROR_TRACES[code_error],
                    message=error_message,
                ),
            ],
        )
