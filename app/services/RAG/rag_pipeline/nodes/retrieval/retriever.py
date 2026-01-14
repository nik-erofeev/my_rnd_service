# import asyncio
import logging
from typing import Literal

# from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

# from app.services.RAG.exceptions import RagPipelineError
from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.rag_pipeline.nodes.base.base_node import BaseNode
from app.services.RAG.rag_pipeline.state import RAGState

# from langchain_huggingface import HuggingFaceEmbeddings
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# from app.utils.logging_decorators import log_execution_time

logger = logging.getLogger(__name__)


class RetrieverIntent(BaseNode):
    """
    Узел, отвечающий за поиск документов.

    Использует LLM для переформулирования запроса (MultiQuery) и выполняет поиск
    в векторной базе данных (в данном случае - моковая реализация).
    """

    # КОНСТАНТЫ для типов поиска
    SEARCH_TYPE_BM25: Literal["bm25"] = "bm25"
    SEARCH_TYPE_VECTOR: Literal["vector"] = "vector"

    # КОНСТАНТЫ для поиска с фильтром в методате, в примере - verify_id
    VERIFY_ID_ALL: Literal["All"] = "All"

    def __init__(
        self,
        llm: AsyncLLM,
        prompt: str,
        ## todo: параметры для embedding/opensearch
        # opensearch: OpenSearchVectorSearch,
        # embedding_model: HuggingFaceEmbeddings,
        ## todo: дрп параметры для векторного поиска
        # k: int,  # Количество чанков для каждого типа поиска
        # n: int,  # Количество генерируемых переформулировок запроса
        # relevance_threshold: float,
        # use_hybrid_search: bool,
        # bm25_weight: float,
    ):
        super().__init__()
        self.llm = llm
        self.prompt = PromptTemplate.from_template(prompt)
        # self.opensearch = opensearch
        # self.embedding_model = embedding_model
        # self.k = k
        # self.n = n
        # self.relevance_threshold = relevance_threshold
        # self.use_hybrid_search = use_hybrid_search
        # self.bm25_weight = bm25_weight

    async def ainvoke(self, state: RAGState) -> RAGState:
        """Основной entrypoint: поиск с фильтром, дедупликация и логирование."""
        logger.info("🔍 RetrieverIntent запущен...")

        main_query, history = self._prepare_queries(state)

        # intent_queries будет использован при включении реального поиска
        intent_queries = self._prepare_intent_queries(state)

        # по тексту запроса получаем ищем документы (например в OpenSearch)

        # ## пример без мока
        # # verify_id = state.get("additional_data", {}).get("verify_id")  # например можно хранить в состоянии
        # verify_id = "All"  # например можно хранить в состоянии
        # retrieved = await self._execute_queries(
        #     main_query=main_query,
        #     intent_queries=intent_queries,
        #     history=history,
        #     verify_id=verify_id,
        # )

        # ## todo: пример с моком!
        prompt = self.prompt.format(message=main_query, history=history)
        response = await self.llm.generate([{"role": "user", "text": str(prompt)}])
        logger.info(f"🔍 LLM ответил: {response.alternatives[-1].message.text}")
        mock_result: list[Document] = [
            Document(
                page_content=f"Какой-то текст с информацией_{i}",
                metadata={
                    "id": str(i),
                    "AdditionalData": {"parentName": f"parentName_{i}"},
                },
            )
            for i in range(1, 4)
        ]
        retrieved = mock_result

        unique_docs = self._deduplicate_docs(retrieved)
        return {"retrieved": unique_docs}

    def _prepare_queries(self, state: RAGState) -> tuple[str, list[str]]:
        """Возвращает основной запрос и историю сообщений."""
        messages = state["messages"]
        main_query = self.process_input_message(messages[-1])
        history = self.process_input_list(messages[:-1])
        return main_query, history

    def _prepare_intent_queries(self, state: RAGState) -> list[str]:
        """Список intent-запросов для дополнительного поиска."""
        last_intent = self._extract_last_intent(state.get("intent"))
        return [last_intent] if last_intent else []

    @staticmethod
    def _extract_last_intent(intent_data: list | None) -> str | None:
        """Возвращает последний intent как строку, если есть."""
        if not intent_data:
            return None
        return str(intent_data[-1])

    def _deduplicate_docs(self, docs: list[Document]) -> list[Document]:
        """Удаляет дубликаты."""
        unique_docs = self.make_chunks_unique(docs)
        logger.info(f"📄 После дедупликации: {len(unique_docs)} уникальных чанков(а)")
        return unique_docs

    @staticmethod
    def make_chunks_unique(chunks: list[Document]) -> list[Document]:
        """Удаляет дубли по содержимому."""
        seen = set()
        unique = []
        for chunk in chunks:
            # Создаем ключ для сравнения
            key = chunk.page_content[:200]
            if key not in seen:
                seen.add(key)
                unique.append(chunk)
        return unique

    # ## todo: ниже пример без мока - раскомментить
    # async def _execute_queries(
    #     self,
    #     main_query: str,
    #     intent_queries: list[str],
    #     history: list[str],
    #     verify_id: list[str] | str,
    # ) -> list[Document]:
    #     """Выполняет поиск по основному и intent-запросам."""
    #     retrieved = await self._a_retrieve_multi(main_query, history, verify_id)
    #     for intent_query in intent_queries:
    #         retrieved.extend(await self._a_retrieve_multi(intent_query, history, verify_id))
    #         logger.info("✅ Дополнительный поиск по intent выполнен")
    #     return retrieved
    #
    # @log_execution_time
    # async def _a_retrieve_multi(
    #     self,
    #     message: str,
    #     history: list[str] | None,
    #     verify_id: list[str] | str,
    # ) -> list[Document]:
    #     """Генерация переформулировок и поиск по каждому запросу."""
    #     history = history or []
    #
    #     filter_clause = self._build_filter_clause(verify_id)
    #
    #     vector_docs: list[Document] = []
    #     bm25_docs: list[Document] = []
    #
    #     for attempt in range(self.n):
    #         try:
    #             llm_query = await self._generate_rewritten_query(message, history)
    #
    #             vector_docs, bm_docs = await self._search_once(
    #                 query=llm_query,
    #                 verify_id=verify_id,
    #                 filter_clause=filter_clause,
    #             )
    #
    #             vector_docs.extend(vector_docs)
    #             bm25_docs.extend(bm_docs)
    #
    #             self._log_iteration_stats(
    #                 attempt=attempt,
    #                 query=llm_query,
    #                 vector_docs=vector_docs,
    #                 bm25_docs=bm_docs,
    #             )
    #
    #         except RagPipelineError:
    #             raise
    #         except Exception as e:
    #             raise RagPipelineError(
    #                 message=f"Ошибка подключения к OpenSearch: {e!r}",
    #             ) from e
    #
    #     all_docs = self._merge_search_results(vector_docs=vector_docs, bm25_docs=bm25_docs)
    #     self._log_pre_dedup_stats(all_docs)
    #
    #     return all_docs
    #
    # async def _generate_rewritten_query(
    #     self,
    #     message: str,
    #     history: list[str],
    # ) -> str:
    #     prompt = self.prompt.format(message=message, history=history)
    #     response = await self.llm.generate(
    #         [{"role": "user", "text": str(prompt)}],
    #     )
    #     return response.alternatives[-1].message.text
    #
    # async def _search_once(
    #     self,
    #     query: str,
    #     verify_id: list[str] | str,
    #     filter_clause: dict | None,
    # ) -> tuple[list[Document], list[Document]]:
    #     """
    #     Выполняет один прогон поиска по одному запросу.
    #     Возвращает:
    #       - list[Document] из vector-поиска
    #       - list[Document] из bm25 (пустой, если hybrid отключён)
    #     """
    #     if not self.use_hybrid_search:
    #         vector_docs = await self._vector_search(query, verify_id, filter_clause)
    #         return vector_docs, []
    #
    #     return await asyncio.gather(
    #         self._vector_search(query, verify_id, filter_clause),
    #         self._bm25_search(query, verify_id, filter_clause),
    #     )
    #
    # def _log_iteration_stats(
    #     self,
    #     attempt: int,
    #     query: str,
    #     vector_docs: list[Document],
    #     bm25_docs: list[Document],
    # ) -> None:
    #     suffix = (
    #         f"{len(vector_docs)} vector + {len(bm25_docs)} bm25"
    #         if self.use_hybrid_search
    #         else f"{len(vector_docs)} vector"
    #     )
    #
    #     logger.info(f"🔍 [{attempt + 1}] Запрос '{query}' — найдено: {suffix}")
    #
    # @staticmethod
    # def _merge_search_results(
    #     vector_docs: list[Document],
    #     bm25_docs: list[Document],
    # ) -> list[Document]:
    #     # В текущей стратегии:
    #     # если vector-поиск не дал результатов — считаем, что релевантных документов нет
    #     if not vector_docs:
    #         return []
    #
    #     return vector_docs + bm25_docs
    #
    # def _log_pre_dedup_stats(self, docs: list[Document]) -> None:
    #     if not docs:
    #         return
    #
    #     stats: dict[str, int] = {}
    #     for doc in docs:
    #         search_type = doc.metadata.get("_search_type", "unknown")
    #         stats[search_type] = stats.get(search_type, 0) + 1
    #
    #     logger.info(
    #         f"📊 ДО дедупликации (по типам поиска): {stats}\n"
    #         f"   💾 Чанки:\n{self._format_docs_info(docs, format_json=False)}",
    #     )
    #
    # @staticmethod
    # def _format_docs_info(docs: list[Document], format_json: bool = True) -> str:
    #     """Форматирует информацию о найденных чанках для логирования.
    #
    #     Args:
    #         docs: Список чанков для форматирования
    #         format_json: Если True - выводит AdditionalData в красивом JSON формате,
    #                     если False - выводит только основную информацию без JSON
    #
    #     Returns:
    #         str: отформатированная строка с информацией о чанках
    #     """
    #     if not docs:
    #         return "нет чанков"
    #
    #     docs_info: list[str] = []
    #
    #     if format_json:
    #         # С JSON форматированием (подробный вывод)
    #         for i, doc in enumerate(docs, 1):
    #             # Получаем ВСЮ AdditionalData из metadata
    #             additional_data = doc.metadata.get("AdditionalData", {})
    #             score = doc.metadata.get("_score", "N/A")
    #             search_type = doc.metadata.get("_search_type", "unknown")
    #
    #             # Форматируем AdditionalData как красиво отформатированный JSON
    #             additional_data_json = json.dumps(additional_data, ensure_ascii=False, indent=2)
    #
    #             docs_info.append(f"  [{i}] score={score} | type={search_type}")
    #             docs_info.append("      AdditionalData:")
    #             # Добавляем JSON с отступом
    #             for line in additional_data_json.split("\n"):
    #                 docs_info.append(f"        {line}")
    #     else:
    #         # БЕЗ JSON форматирования (краткий вывод)
    #         for i, doc in enumerate(docs, 1):
    #             score = doc.metadata.get("_score", "N/A")
    #             search_type = doc.metadata.get("_search_type", "unknown")
    #
    #             # Получаем только основные поля из AdditionalData
    #             additional_data = doc.metadata.get("AdditionalData", {})
    #             card_id = additional_data.get("cardId", "N/A")
    #
    #             docs_info.append(
    #                 f"  [{i}] score={score} | type={search_type} | cardId={card_id} | AdditionalData={additional_data}",  # noqa: E501
    #             )
    #
    #     return "\n".join(docs_info)
    #
    # @log_execution_time
    # async def _vector_search(
    #     self,
    #     query_text: str,
    #     verify_id: list[str] | str,
    #     filter_clause: dict | None = None,
    # ) -> list[Document]:
    #     """Векторный поиск."""
    #     return await self._search(
    #         mode=self.SEARCH_TYPE_VECTOR,
    #         query_text=query_text,
    #         verify_id=verify_id,
    #         filter_clause=filter_clause,
    #     )
    #
    # async def _search(
    #     self,
    #     mode: str,
    #     query_text: str,
    #     verify_id: list[str] | str,
    #     filter_clause: dict | None = None,
    # ) -> list[Document]:
    #     """Универсальный поиск по BM25 или Vector."""
    #     try:
    #         # Используем переданный filter_clause (или строим, если не передан)
    #         if filter_clause is None:
    #             filter_clause = self._build_filter_clause(verify_id)
    #
    #         if mode == self.SEARCH_TYPE_BM25:
    #             body = self._build_bm25_query(query_text=query_text, filter_clause=filter_clause, verify_id=verify_id)
    #             response = await self.opensearch.async_client.search(
    #                 index=self.opensearch.index_name,
    #                 body=body,
    #             )
    #             docs = self._process_search_results(response=response, search_type=self.SEARCH_TYPE_BM25)
    #
    #             logger.info(f"✅ BM25: найдено {len(docs)} чанков(а)")
    #             logger.info(f"📄 Чанк(и) BM25:\n{self._format_docs_info(docs=docs, format_json=False)}")
    #             return docs
    #
    #         if mode == self.SEARCH_TYPE_VECTOR:
    #             query_embedding = await self.embedding_model.aembed_query(query_text)
    #             body = self._build_vector_query(
    #                 query_embedding=query_embedding,
    #                 filter_clause=filter_clause,
    #                 verify_id=verify_id,
    #             )
    #             response = await self.execute_search(body=body, mode=mode)
    #             docs = self._process_search_results(response=response, search_type=self.SEARCH_TYPE_VECTOR)
    #
    #             logger.info(f"✅ Vector: найдено {len(docs)} чанков(а)")
    #             logger.info(f"📄 Чанки Vector:\n{self._format_docs_info(docs=docs, format_json=False)}")
    #             return docs
    #
    #         # иначе
    #         raise ValueError(f"Неизвестный режим поиска: {mode}")
    #
    #     except RagPipelineError:
    #         raise
    #     except Exception as e:
    #         logger.error(f"Ошибка в _search ({mode}): {e}")
    #         raise RagPipelineError(
    #             message=f"Ошибка при поиске ({mode}): {e!r}",
    #         ) from e
    #
    # def _build_filter_clause(self, verify_id: list[str] | str) -> dict | None:
    #     """Строит OpenSearch filter clause по verify_id.
    #
    #     Returns:
    #         dict: {"terms": {"metadata.AdditionalData.cardId.keyword": [...]}}
    #         None: если фильтр не нужен
    #     """
    #
    #     # СЛУЧАЙ 1: verify_id == "All" → БЕЗ ФИЛЬТРА
    #     if verify_id == self.VERIFY_ID_ALL:
    #         logger.info("📋 Фильтр по verify_id: 'All' → БЕЗ ФИЛЬТРА")
    #         return None
    #
    #     # СЛУЧАЙ 2: verify_id == ["card_1", "card_2", ...] → С ФИЛЬТРОМ
    #     if isinstance(verify_id, list):
    #         filter_clause = {"terms": {"metadata.AdditionalData.cardId.keyword": verify_id}}
    #         logger.info(f"📋 Фильтр по verify_id: {verify_id} → С ФИЛЬТРОМ")
    #         return filter_clause
    #
    #     # СЛУЧАЙ 3: verify_id == None или другое неизвестное значение → ОШИБКА
    #     else:
    #         logger.error(f"❌ verify_id имеет неожиданное значение: {verify_id}")
    #         raise RagPipelineError(
    #             message=f"Ошибка при построении фильтра: verify_id={verify_id} (ожидается '{self.VERIFY_ID_ALL}' или список)",  # noqa: E501
    #         )
    #
    # @staticmethod
    # def _process_search_results(response: dict, search_type: str) -> list[Document]:
    #     """Обрабатывает результаты поиска OpenSearch в Document объекты."""
    #     return [
    #         Document(
    #             page_content=hit["_source"]["text"],
    #             metadata={
    #                 **hit["_source"].get("metadata", {}),
    #                 "_search_type": search_type,
    #                 "_score": float(hit["_score"]),
    #             },
    #         )
    #         for hit in response.get("hits", {}).get("hits", [])
    #     ]
    #
    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_exponential(multiplier=1, min=0.5, max=5),
    #     retry=retry_if_exception_type(Exception),
    #     reraise=True,
    # )
    # async def execute_search(self, body: dict, mode: Literal["vector", "bm25"]) -> dict:
    #     try:
    #         return await self.opensearch.async_client.search(index=self.opensearch.index_name, body=body)
    #     except Exception as e:
    #         raise RagPipelineError(message=f"Ошибка при поиске(execute_search) ({mode}): {e!r}") from e
    #
    # def _build_vector_query(
    #     self,
    #     query_embedding: list[float],
    #     filter_clause: dict | None,
    #     verify_id: list[str] | str,
    # ) -> dict:
    #     """Строит Vector KNN query для OpenSearch."""
    #     size = int(self.k * (1 - self.bm25_weight)) or 1  # чтобы size не стал 0
    #
    #     if verify_id == self.VERIFY_ID_ALL:
    #         logger.info("🔓 _build_vector_query: verify_id='All' → query.knn без filter (БЕЗ ФИЛЬТРА)")
    #         body = {
    #             "size": size,
    #             "query": {
    #                 "knn": {
    #                     "vector_field": {
    #                         "vector": query_embedding,
    #                         "k": 4,
    #                     },
    #                 },
    #             },
    #             "min_score": self.relevance_threshold,
    #         }
    #     # ВАРИАНТ 2 (С ФИЛЬТРОМ):
    #     else:
    #         logger.info(
    #             f"🔒 _build_vector_query: verify_id={verify_id} → bool.must(knn).filter (С ФИЛЬТРОМ)",
    #         )
    #         body = {
    #             "size": size,
    #             "query": {
    #                 "bool": {
    #                     "must": [
    #                         {
    #                             "knn": {
    #                                 "vector_field": {
    #                                     "vector": query_embedding,
    #                                     "k": 4,
    #                                 },
    #                             },
    #                         },
    #                     ],
    #                     "filter": [filter_clause],
    #                 },
    #             },
    #             "min_score": self.relevance_threshold,
    #         }
    #
    #     return body
    #
    # def _build_bm25_query(self, query_text: str, filter_clause: dict | None, verify_id: list[str] | str) -> dict:
    #     """Строит BM25 query для OpenSearch.
    #     Returns:
    #         dict: query body для OpenSearch
    #     """
    #     size = int(self.k * self.bm25_weight)
    #
    #     if verify_id == self.VERIFY_ID_ALL:
    #         logger.info("🔓 _build_bm25_query: verify_id='All' → match query (БЕЗ ФИЛЬТРА)")
    #         return {
    #             "size": size,
    #             "query": {
    #                 "match": {
    #                     "text": query_text,
    #                 },
    #             },
    #         }
    #     else:
    #         # С ФИЛЬТРОМ: bool query с must + filter
    #         logger.info(f"🔒 _build_bm25_query: verify_id={verify_id} → bool query (С ФИЛЬТРОМ)")
    #         return {
    #             "size": size,
    #             "query": {
    #                 "bool": {
    #                     "must": [
    #                         {
    #                             "match": {
    #                                 "text": query_text,
    #                             },
    #                         },
    #                     ],
    #                     "filter": [filter_clause],  # ← list[dict] ОК для bool
    #                 },
    #             },
    #         }
    #
    # @log_execution_time
    # async def _bm25_search(
    #     self,
    #     query_text: str,
    #     verify_id: list[str] | str,
    #     filter_clause: dict | None = None,
    # ) -> list[Document]:
    #     """BM25 поиск."""
    #     return await self._search(
    #         mode=self.SEARCH_TYPE_BM25,
    #         query_text=query_text,
    #         verify_id=verify_id,
    #         filter_clause=filter_clause,
    #     )
