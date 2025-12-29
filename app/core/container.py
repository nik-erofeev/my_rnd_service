import logging

from app.core.config import EnvConfig
from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.rag_pipeline.graph.builder import RAGGraphBuilder
from app.services.RAG.rag_pipeline.pipeline import RAGPipeline
from app.services.rag_service import RagService

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Контейнер зависимостей RAG-сервиса.
    Отвечает за инициализацию и жизненный цикл компонентов RAG (LLM, Pipeline, Graph).
    """

    def __init__(self, config: EnvConfig):
        self.config = config
        self._llm: AsyncLLM | None = None
        self._pipeline: RAGPipeline | None = None
        self._service: RagService | None = None

    # -------- ЛЕНИВЫЕ КОМПОНЕНТЫ --------

    @property
    def llm(self) -> AsyncLLM:
        if self._llm is None:
            logger.info("🔧 Инициализация LLM...")
            # Здесь можно передать конфиг в LLM если нужно
            self._llm = AsyncLLM()
            logger.info("✅ LLM инициализирован")
        return self._llm

    @property
    def pipeline(self) -> RAGPipeline:
        if self._pipeline is None:
            logger.info("🔧 Сборка RAG графа...")
            graph_builder = RAGGraphBuilder(async_llm=self.llm, use_answer_checker=True)
            self._pipeline = RAGPipeline(graph=graph_builder.build())
            logger.info("✅ RAG граф собран")
        return self._pipeline

    @property
    def service(self) -> RagService:
        if self._service is None:
            logger.info("🚀 Сборка RAG сервиса...")
            self._service = RagService(pipeline=self.pipeline)
            logger.info("🎉 RAG сервис готов")
        return self._service

    # -------- ПУБЛИЧНЫЕ МЕТОДЫ --------

    async def init_async(self) -> None:
        """Асинхронная инициализация ресурсов."""
        # Пример: проверка соединения с LLM или VectorDB
        logger.info("🔧 Асинхронная инициализация ресурсов...")
        pass

    def build_service(self) -> RagService:
        return self.service

    async def aclose(self) -> None:
        """Закрытие ресурсов."""
        logger.info("🔻 Закрытие ресурсов контейнера...")
        # Если есть клиенты сессий (aiohttp), закрываем их здесь
        pass
