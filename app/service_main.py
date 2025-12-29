# my_rnd_service/app/service_main.py
from __future__ import annotations
import logging
from datetime import datetime
from typing import Annotated, Any

from faststream import FastStream, Depends, Context

from app.core.config import CONFIG

# 
from app.services.rag_service import RagService
# 
from app.core.logger.logger import setup_logger, get_logger

# 
from app.core.kafka_broker.brokers import broker, registry
from app.core.kafka_broker.schemas import LangchainConsumerMessage, LangchainProducerMessage
# 
from faststream.kafka import KafkaBroker
from faststream.asgi import AsgiFastStream, make_ping_asgi
from prometheus_client import make_asgi_app

# 
setup_logger(CONFIG)
# 
logger = get_logger(__name__)

SERVICE_KEY = "service"


# =============================================================================
#  LIFESPAN
# =============================================================================
from contextlib import asynccontextmanager
from app.core.container import DependencyContainer

@asynccontextmanager
async def lifespan():
    """
    Lifespan сервиса.
    Startup: создаёт контейнер, инициализирует ресурсы, строит сервис.
    Shutdown: закрывает ресурсы контейнера.
    """
    logger.info("🔧 Запуск DependencyContainer...")
    container = DependencyContainer(config=CONFIG)

    await container.init_async()
    service_instance: RagService = container.build_service()

    # Сохраняем сервис в контекст приложения
    app.context.set_global(SERVICE_KEY, service_instance)
    logger.info("✅ Сервис инициализирован и сохранён в контексте")

    try:
        yield
    finally:
        logger.info("💤 Остановка сервиса. Освобождение ресурсов...")
        await container.aclose()


# 
@broker.subscriber(
    CONFIG.read_kafka.topic_in,
    group_id=CONFIG.read_kafka.group_id,
    max_workers=CONFIG.read_kafka.max_workers,
)
async def on_message(
    body: LangchainConsumerMessage,
    headers: Annotated[dict[str, Any], Context("message.headers")],
    key: Annotated[bytes, Context("message.raw_message.key")],
    service: Annotated[RagService, Context(SERVICE_KEY)],
) -> LangchainProducerMessage:
    # Middleware (AutoPublishMiddleware) автоматически опубликует результат
    return await service.handle_message(body=body, headers=headers, key=key)


app = AsgiFastStream(
    broker,
    logger=logger,
    lifespan=lifespan,
    asgi_routes=[
        ("/health", make_ping_asgi(broker)),
        ("/metrics", make_asgi_app(registry)),
    ],
)
# 


# =============================================================================
#  ЛОГИ СТАРТА/СТОПА
# =============================================================================
# @app.on_startup  # ДО подключения к брокеру
@app.after_startup  # ПОСЛЕ подключения к брокеру
async def example_log_start() -> None:
    # по дефолту в FastStream logger установлен в warning(нужно задавать через BasicConfig.level=INFO)
    # мы ужа задали в setup_logger

    logger.info("🚀 - FastStream приложение запущено. Подключение к кафке установлено")
    logger.info("Запуск сервиса в %s с конфигурацией:", datetime.now())
    logger.info("  - Топик чтения: %s", CONFIG.read_kafka.topic_in)
    logger.info("  - Топик записи: %s", CONFIG.write_kafka.topic_out)


@app.on_shutdown
async def example_log_stop() -> None:
    logger.info("💤- FastStream приложение остановлено. Работа завершена")


if __name__ == "__main__":
    # через CLI - в контейнере # todo: важно
    # faststream run app.service_main:app --host 0.0.0.0 --port 8080
    # faststream run app.service_main:app --host 0.0.0.0 --port 8080 --reload # для разработки
    # todo: uvicorn - пробы ручек не принтятся в контейнере с warning
    # uvicorn app.service_main:app --host 0.0.0.0 --port 8080 --log-level warning
    # uvicorn app.service_main:app --host 0.0.0.0 --port 8080 --log-level info # для теста - будут принтятся

    import uvicorn
    import asyncio

    # asyncio.run(app.run())  # todo: debug
    # Запуск через uvicorn, так как это теперь ASGI приложение
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        # log_level="info",
        log_level="critical",
    )
