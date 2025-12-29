"""Реализация эндпоинта для отправки запроса к модели. Это пример"""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import ORJSONResponse

from app.api.example.schemas import ModelRequest, ModelResponse
from app.core.config import CONFIG
from app.core.kafka_broker.brokers import broker

logger = logging.getLogger("app")

router = APIRouter(
    tags=["predict"],
    prefix=f"{CONFIG.api.v1}/predict",
)


@router.post(
    "/",
    response_model=ModelResponse,
    response_class=ORJSONResponse,
    summary="Тест эндпоинт для генерации текста с помощью модели",
    status_code=status.HTTP_201_CREATED,
)
async def generate_text(request: ModelRequest) -> ModelResponse:
    """
    Эндпоинт для генерации текста с помощью модели

    Args:
        request (ModelRequest): Запрос с параметрами генерации

    Returns:
        ModelResponse: Сгенерированный текст и время обработки
    """
    try:
        logger.info(f"Получен запрос: {request.text}")

        generated_text = "Ответ модели"

        logger.info("Текст успешно сгенерирован")

        return ModelResponse(generated_text=generated_text)

    except Exception as e:
        logger.error(f"Ошибка при генерации текста: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации текста: {str(e)}") from e


example_publisher = broker.publisher(CONFIG.api.topik)


@router.post(
    "/faststream",
    response_model=ModelResponse,
    response_class=ORJSONResponse,
    summary="Тест эндпоинт для отправки mess в кафку",
    status_code=status.HTTP_201_CREATED,
)
async def generate_faststream(request: ModelRequest) -> ModelResponse:
    """
    Эндпоинт для отправки mess в кафку

    Args:
        request (ModelRequest): Запрос с параметрами генерации

    Returns:
        ModelResponse: Сгенерированный текст и время обработки
    """
    try:
        logger.info(f"Получен запрос: {request.text}")

        kafka_text = f"сообщение в кафку: {request.text}"
        kafka_json = {"text": kafka_text}

        await example_publisher.publish(message=kafka_json)
        logger.info("Текст успешно отправлен в кафку")

        return ModelResponse(generated_text=kafka_text)

    except Exception as e:
        logger.error(f"Ошибка при генерации текста: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации текста: {str(e)}") from e
