from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.default.routers import router as default_router
from app.api.example.routers import router as example_router
from app.core.config import CONFIG, EnvConfig
from app.core.kafka_broker.brokers import broker
from app.core.logger.logger import get_logger, setup_logger

setup_logger(CONFIG)
logger = get_logger(__name__)


def _init_routes(app: FastAPI) -> None:
    """Подключение всех роутеров к приложению.

    Args:
        app: Экземпляр FastAPI, к которому нужно подключить роутеры
    """
    routers = [
        example_router,
        default_router,
    ]
    for router in routers:
        app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.

    Код ДО yield выполняется при STARTUP (инициализация)
    Код ПОСЛЕ yield выполняется при SHUTDOWN (очистка)

    Это заменяет deprecated:
        @app.on_event("startup")
        @app.on_event("shutdown")
    """
    # ============= STARTUP (код ДО yield) =============
    logger.info("web_main: инициализация приложения...")
    try:
        await broker.start()
        logger.info("✅ Подключение к Kafka брокеру успешно установлено")
        # Принудительно подключаемся к Kafka
        # logger.info("🔗 Принудительно подключаемся к Kafka...")
        # await broker.connect()

    except Exception as e:
        logger.error(f"❌ Ошибка запуска брокера: {e}")
        raise

    # Здесь инициализируем ресурсы:
    # - Подключаемся к БД
    # - Загружаем модели ML
    # - Инициализируем кэши
    # - Запускаем background tasks

    # EXAMPLE
    # Initialize database connection pool
    # try:
    #     app.state.database_pool = create_async_engine(
    #         str(APP_CONFIG.db.sqlalchemy_db_uri),
    #         echo=APP_CONFIG.db.echo,
    #     )
    #     app.state.session_maker = async_sessionmaker(
    #         app.state.database_pool,
    #         class_=AsyncSession,
    #         expire_on_commit=False,
    #     )
    #     logger.info("✅ Database connection pool initialized successfully")
    # except Exception as e:
    #     logger.error(f"❌ Failed to initialize database connection pool: {e}")
    #     raise
    #
    # # Initialize Kafka broker
    # try:
    #     await broker.start()
    #     logger.info("✅ Подключение к Kafka брокеру успешно установлено")
    #     # Принудительно подключаемся к Kafka
    #     # logger.info("🔗 Принудительно подключаемся к Kafka...")
    #     # await broker.connect()
    #
    # except Exception as e:
    #     logger.error(f"❌ Ошибка запуска брокера: {e}")
    #     raise

    logger.info("🚀 web_main: FastAPI приложение запущено.")

    # yield - передаем управление приложению
    try:
        yield
    finally:
        # ============= SHUTDOWN (код ПОСЛЕ yield) =============
        logger.info("web_main: очистка ресурсов при завершении...")

        # Здесь очищаем ресурсы:
        # - Закрываем подключение к БД
        # - Останавливаем background tasks
        # - Сохраняем кэши
        # - Освобождаем память

        try:
            await broker.stop()
            logger.info("✅ Kafka брокер успешно остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки брокера: {e}")
        logger.info("✅ Приложение остановлено.")
        # EXAMPLE
        # Close database connection pool
        # try:
        #     await app.state.database_pool.dispose()
        #     logger.info("✅ Database connection pool closed successfully")
        # except Exception as e:
        #     logger.error(f"❌ Failed to close database connection pool: {e}")
        #
        # # Stop Kafka broker
        # try:
        #     await broker.stop()
        #     logger.info("✅ Kafka брокер успешно остановлен")
        # except Exception as e:
        #     logger.error(f"❌ Ошибка остановки брокера: {e}")

        logger.info("💤 web_main: FastAPI приложение остановлено. Работа завершена")


def create_app(config: EnvConfig) -> FastAPI:
    """
    Создание и конфигурация FastAPI приложения.

    Returns:
        Сконфигурированное приложение FastAPI
    """
    app_ = FastAPI(
        title=config.api.project_name,
        version=config.api.version,
        description=config.api.description,
        contact={"name": "Example", "email": "example@example.com"},
        openapi_url=config.api.openapi_url,
        debug=config.api.echo,
        lifespan=lifespan,
    )

    app_.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # # эндпоинт для отображения метрик для их дальнейшего сбора Прометеусом
    # from prometheus_fastapi_instrumentator import Instrumentator
    # instrumentator = Instrumentator(
    #     should_group_status_codes=False,
    #     excluded_handlers=[".*admin.*", "/metrics"],
    # )
    # instrumentator.instrument(app_).expose(
    #     app_,
    #     include_in_schema=True,
    # )  # можно выкл

    _init_routes(app_)

    @app_.exception_handler(Exception)
    async def http_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(f"❌Произошла непредвиденная ошибка: {exc=!r}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Произошла непредвиденная ошибка"},
        )

    @app_.get("/")
    def root() -> RedirectResponse:
        # return {"message": "Example API(перейдите на /docs) 🚀"}
        return RedirectResponse(url="/docs")

    return app_


app = create_app(CONFIG)

# Через CLI запускать так:
# uvicorn app.web_main:app --host 0.0.0.0 --port 8080 --log-level info
# uvicorn app.web_main:app --host 0.0.0.0 --port 8080 --reload

# Либо запускаем из воркера
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web_main:app",
        host=CONFIG.api.host,
        port=CONFIG.api.port,
        reload=CONFIG.api.debug,
        log_level="info",  # Чтобы не переопределял логгер
    )
