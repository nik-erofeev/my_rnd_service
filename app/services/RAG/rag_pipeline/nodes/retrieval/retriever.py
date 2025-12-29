import logging

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.rag_pipeline.nodes.base.base_node import BaseNode
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class RetrieverIntent(BaseNode):
    """
    Узел, отвечающий за поиск документов.

    Использует LLM для переформулирования запроса (MultiQuery) и выполняет поиск
    в векторной базе данных (в данном случае - моковая реализация).
    """

    def __init__(
        self,
        llm: AsyncLLM,
        prompt: str,
    ):
        super().__init__()
        self.llm = llm
        self.prompt = PromptTemplate.from_template(prompt)

    def _prepare_queries(self, state: RAGState) -> tuple[str, list[str]]:
        """Возвращает основной запрос и историю сообщений."""
        main_query = self.process_input_message(state["messages"][-1])
        history = self.process_input_list(state["messages"][:-1])
        return main_query, history

    async def ainvoke(self, state: RAGState) -> RAGState:
        """Основной entrypoint: поиск с фильтром, дедупликация и логирование."""
        logger.info("🔍 RetrieverIntent запущен...")
        main_query, history = self._prepare_queries(state)

        prompt = self.prompt.format(message=main_query, history=history)
        response = await self.llm.generate([{"role": "user", "text": str(prompt)}])

        llm_query = response.alternatives[-1].message.text
        logger.info(f"🔍 LLM ответил: {llm_query}")

        # по тексту запроса получаем ищем документы (например в OpenSearch)

        data_list: list[Document] = [
            Document(
                page_content=f"Какой-то текст с информацией_{i}",
                metadata={
                    "id": str(i),
                    "AdditionalData": {"parentName": f"parentName_{i}"},
                },
            )
            for i in range(1, 4)
        ]

        return {"retrieved": data_list}
