import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

from app.services.RAG.exceptions import RagPipelineError
from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.llm.schemas import ResponseYAGPTSchema
from app.services.RAG.rag_pipeline.nodes.base.base_node import BaseNode
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class BaseLLM(BaseNode):
    """Базовый класс для работы с LLM через YandexGPT API.

    Предоставляет общую логику для генерации ответов с использованием промптов.
    """

    def __init__(
        self,
        llm: AsyncLLM,
        prompt: str,
    ):
        """Инициализация базового LLM.

        Args:
            llm: Процессор для генерации ответов
            prompt: Шаблон промпта для запросов
        """
        super().__init__()
        self.prompt = PromptTemplate.from_template(prompt)
        self.llm = llm

    @staticmethod
    def process_output(x: ResponseYAGPTSchema) -> AIMessage:
        """Обрабатывает ответ генератора в сообщение AI.

        Args:
            x: Ответ от генератора

        Returns:
            Сообщение AI с извлеченным текстом
        """
        # контракт AsyncGenerateProcessor должен гарантировать структуру!!!
        return AIMessage(x.alternatives[-1].message.text, name="ai")

    @staticmethod
    def _format_context(retrieved: list[Any]) -> str:
        """Форматирует найденные документы в строку для промпта.

        Args:
            retrieved: Список найденных документов или строк

        Returns:
            Отформатированная строка с контекстом
        """
        if not retrieved:
            return "Нет релевантных документов."
        # Если это Document — форматируем
        if hasattr(retrieved[0], "page_content"):
            parts = []
            for doc in retrieved:
                # Получаем имя родительского документа из метаданных
                name = doc.metadata.get("AdditionalData", {}).get("parentName", "Unknown")
                content = doc.page_content.replace("\n", " ")
                parts.append(f"Документ {name}: {content}")
            return "\n\n".join(parts)
        else:
            # Если это строки (старый режим) — просто объединяем
            return "\n\n".join(str(x) for x in retrieved)

    async def ainvoke(self, state: RAGState) -> RAGState:  # ← async
        logger.info("BaseLLM start wait...")
        context_str = self._format_context(state["retrieved"])
        logger.debug(f"context_str: \n {context_str}")
        prompt = str(
            self.prompt.format(
                message=self.process_input_message(state["messages"][-1]),
                history=self.process_input_list(state["messages"][:-1]),
                context=context_str,
            ),
        )
        try:
            generate_result = await self.llm.generate([{"role": "user", "text": prompt}])
        except RagPipelineError:
            # Уже обработанные - пробрасываем выше
            raise

        response = self.process_output(generate_result)
        logger.info("BaseLLM end")
        return {
            "messages": [response],
            "retrieved": state["retrieved"],
            "intent": state["intent"],
        }
