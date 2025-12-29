from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.kafka_broker.schemas import LangchainConsumerMessage, LangchainProducerMessage, StatusCode
from app.services.rag_service import RagService


@pytest.fixture
def mock_pipeline():
    """Фикстура для создания мока пайплайна."""
    pipeline = Mock()
    # Настраиваем дефолтное поведение для query - возвращает структуру с сообщением
    mock_message = Mock()
    mock_message.content = "result pipeline"
    pipeline.query = AsyncMock(return_value={"messages": [mock_message]})
    return pipeline


@pytest.fixture
def rag_service(mock_pipeline: Mock) -> RagService:
    """Фикстура для создания сервиса с моком пайплайна."""
    return RagService(pipeline=mock_pipeline)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, expected_answer",
    [
        ("какая-то странная фраза", "result pipeline"),
        ("другой вопрос", "result pipeline"),  # Mock возвращает одно и то же
    ],
)
async def test_rag_service_handle_message_success(
    rag_service: RagService,
    mock_pipeline: Mock,
    question: str,
    expected_answer: str,
) -> None:
    """Тест успешной обработки сообщения RagService с параметризацией."""
    body = LangchainConsumerMessage(test_questions=question)
    headers: dict[str, Any] = {}
    key = b"rag_key"

    result = await rag_service.handle_message(body=body, headers=headers, key=key)

    # Проверяем, что pipeline.query был вызван с переданным вопросом
    mock_pipeline.query.assert_called_once_with(question)

    # Вариант 1: Проверка всего объекта
    assert result == LangchainProducerMessage(message=expected_answer, statusCode=StatusCode.SUCCESS)

    # Вариант 2: Построчная проверка полей
    assert result.message == expected_answer
    assert result.statusCode == StatusCode.SUCCESS


@pytest.mark.asyncio
async def test_rag_service_handle_message_exception(rag_service: RagService, mock_pipeline: Mock) -> None:
    """Тест обработки исключения в RagService."""

    # Переопределяем поведение мока для генерации ошибки
    mock_pipeline.query.side_effect = Exception("pipeline failed")

    body = LangchainConsumerMessage(test_questions="какая-то странная фраза")
    headers: dict[str, Any] = {}
    key = b"rag_key"

    try:
        await rag_service.handle_message(body=body, headers=headers, key=key)
    except Exception as e:
        assert "pipeline failed" in str(e)
