import logging

from app.core.config import EnvConfig
from app.services.RAG.llm.llm import AsyncLLM

# from app.services.RAG.rag_pipeline.embeddings.embedding import Embedding
from app.services.RAG.rag_pipeline.graph.builder import RAGGraphBuilder
from app.services.RAG.rag_pipeline.pipeline import RAGPipeline
from app.services.rag_service import RagService

# from pathlib import Path

# from langchain_community.vectorstores import OpenSearchVectorSearch
# from langchain_huggingface import HuggingFaceEmbeddings


logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Контейнер зависимостей RAG-сервиса.
    Отвечает за инициализацию и жизненный цикл компонентов RAG (LLM, Pipeline, Graph).
    """

    def __init__(self, config: EnvConfig):
        self.config = config
        self._llm: AsyncLLM | None = None
        # self._embeddings: HuggingFaceEmbeddings | None = None
        # self._opensearch: OpenSearchVectorSearch | None = None
        self._graph_builder: RAGGraphBuilder | None = None
        self._pipeline: RAGPipeline | None = None
        self._service: RagService | None = None

    # -------- ЛЕНИВЫЕ КОМПОНЕНТЫ --------
    # @property
    # def embeddings(self) -> HuggingFaceEmbeddings:
    #     """Инициализация модели эмбеддингов"""
    #     if self._embeddings is None:
    #         # Извлекаем название модели из пути
    #         model_path = self.config.embedding.model
    #         model_name = Path(model_path).name
    #
    #         logger.info(f"🔧 Инициализация модели embeddings: {model_name}...")
    #         embedding_service = Embedding(self.config.embedding)
    #         self._embeddings = embedding_service.embeddings
    #         logger.info(
    #             f"✅ Модель embeddings: {model_name} инициализирована. device: {self.config.embedding.device}",
    #         )
    #     return self._embeddings
    #
    # @property
    # def opensearch(self) -> OpenSearchVectorSearch:
    #     """Инициализация векторного хранилища OpenSearch."""
    #     if self._opensearch is None:
    #         logger.info("🔧 Инициализация OpenSearchVectorSearch...")
    #         self._opensearch = OpenSearchVectorSearch(
    #             opensearch_url=self.config.open_search.url,
    #             index_name=self.config.open_search.index_name,
    #             embedding_function=self.embeddings,
    #             http_auth=(self.config.open_search.login, self.config.open_search.password),
    #             use_ssl=True,
    #             verify_certs=False,
    #             ssl_assert_hostname=False,
    #             ssl_show_warn=False,
    #         )
    #         logger.info("✅ OpenSearchVectorSearch готов к работе")
    #     return self._opensearch

    @property
    def llm(self) -> AsyncLLM:
        """Инициализация LLM."""
        if self._llm is None:
            logger.info("🔧 Инициализация LLM...")
            # Здесь можно передать конфиг в LLM если нужно
            # # todo: vrm
            # self._llm = AsyncLLM(
            #     epa_token_config=self.config.epa_token,
            #     tyk_yandex_config=self.config.tyk_yandex_config,
            #     rnd_token_manager_config=self.config.rnd_token_manager_config,
            #     rnd_yandex_config=self.config.rnd_yandex_config,
            #     use_tyk=self.config.tyk_yandex_config.use_tyk,
            # )

            ## todo: local
            import os

            from dotenv import load_dotenv

            from app.services.RAG.llm.llm import LocalAsyncYandexLLM  # type: ignore

            load_dotenv()
            # local yandex
            self._llm = LocalAsyncYandexLLM(  # noqa
                api_key=os.environ["YC_API_KEY"],
                folder_id=os.environ["YC_FOLDER_ID"],
                model="yandexgpt-lite",
                url="https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            )
            ## ollama
            # self._llm = LocalAsyncOllamaLLM(model="mistral")
            ## todo: local end
            logger.info("✅ LLM инициализирован")
        return self._llm

    @property
    def graph_builder(self) -> RAGGraphBuilder:
        """Возвращает RAGGraphBuilder для доступа к методам build, get_image_graph и т.д."""
        if self._graph_builder is None:
            logger.info("🔧 Создание RAGGraphBuilder...")
            self._graph_builder = RAGGraphBuilder(
                async_llm=self.llm,
                rag_config=self.config.rag,
                # opensearch=self.opensearch,
                # embedding_model=self.embeddings,
            )
            logger.info("✅ RAGGraphBuilder создан")
        return self._graph_builder

    @property
    def pipeline(self) -> RAGPipeline:
        """Инициализация RAG Pipeline с скомпилированным графом."""
        if self._pipeline is None:
            logger.info("🔧 Сборка RAG графа...")
            # builder для получения скомпилированного графа
            compiled_graph = self.graph_builder.build()
            self._pipeline = RAGPipeline(graph=compiled_graph)
            logger.info("✅ RAG граф собран")
        return self._pipeline

    @property
    def service(self) -> RagService:
        """Инициализация RAG Service."""
        if self._service is None:
            logger.info("🚀 Сборка RAG сервиса...")
            self._service = RagService(pipeline=self.pipeline)
            logger.info("✅ RAG сервис готов")
        return self._service

    # -------- ПУБЛИЧНЫЕ МЕТОДЫ --------

    async def init_async(self) -> None:
        """Асинхронная инициализация ресурсов."""
        logger.info("🔧 Асинхронная инициализация ресурсов...")
        # Пример: проверка соединения с LLM или VectorDB
        _ = self.service  # Принудительно инициализировать весь граф

    def build_service(self) -> RagService:
        """Возвращает готовый RagService."""
        return self.service

    async def aclose(self) -> None:
        """Закрытие ресурсов."""
        logger.info("🔻 Закрытие ресурсов контейнера...")
        # Если есть клиенты сессий (aiohttp), закрываем их здесь
        # if self._opensearch is not None:
        #     try:
        #         await self._opensearch.async_client.close()
        #         logger.info("✅ OpenSearch async_client закрыт")
        #     except Exception as e:
        #         logger.warning(f"⚠️ Ошибка при закрытии OpenSearch client: {e}")
