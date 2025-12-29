from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import ORJSONResponse

from app.api.default.schemas import ExcResponse, HealthResponse
from app.core.config import CONFIG
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    # prefix=f"{CONFIG.api.v1}/default",
    tags=["health"],
)


# Health
@router.get(
    "/live",
    response_model=HealthResponse,
    response_class=ORJSONResponse,
    summary="Проверка сервиса на жизнеспособность",
    status_code=status.HTTP_200_OK,
)
def health_live() -> HealthResponse:
    """
    Эндпоинт для проверки сервиса на жизнеспособность.

    Returns:
        HealthResponse: Информация о состоянии сервиса
    """
    logger.info("health")
    return HealthResponse(
        status="ok",
        version=CONFIG.project.version,
        service=CONFIG.project.name,
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    response_class=ORJSONResponse,
    summary="Проверка доступности сервиса",
    status_code=status.HTTP_200_OK,
)
def health_ready() -> HealthResponse:
    """
    Эндпоинт для проверки доступности сервиса.

    Returns:
        HealthResponse: Информация о состоянии сервиса
    """
    # добавить проверки на коннект к бд/флюенту и тд
    # уже после генерации проекта
    logger.info("ready")
    return HealthResponse(
        status="ready",
        version=CONFIG.api.version,
        service=CONFIG.api.project_name,
    )


@router.get(
    "/exception",
    include_in_schema=True,
    response_model=ExcResponse,
    response_class=ORJSONResponse,
    summary="Отправка тест ошибки",
    status_code=status.HTTP_200_OK,
)
async def _exception() -> Any:
    """Роутер для отправки тест ошибки (debug test)"""
    try:
        return 1 / 0
    except ZeroDivisionError as e:
        logger.exception(f"Use exception {e=!r}")
        raise
