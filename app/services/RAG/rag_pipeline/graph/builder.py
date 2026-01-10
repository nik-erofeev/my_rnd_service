import logging

from IPython.display import Image, display
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.rag_pipeline.nodes.base.base_llm import BaseLLM
from app.services.RAG.rag_pipeline.nodes.postprocessing.answer_checker import AnswerChecker
from app.services.RAG.rag_pipeline.nodes.preprocessing.intent import IntentClassifier
from app.services.RAG.rag_pipeline.nodes.preprocessing.router import DocsCounter
from app.services.RAG.rag_pipeline.nodes.retrieval.reranker import Reranker
from app.services.RAG.rag_pipeline.nodes.retrieval.retriever import RetrieverIntent
from app.services.RAG.rag_pipeline.state import RAGState
from app.services.RAG.rag_pipeline.utils.prompts.manager import PromptManager

logger = logging.getLogger(__name__)


class RAGGraphBuilder:
    """Строит LangGraph-граф для RAG-пайплайна."""

    def __init__(self, async_llm: AsyncLLM, use_answer_checker: bool = True):
        """
        Инициализирует строитель графа.

        Args:
            async_llm (AsyncLLM): Экземпляр асинхронной LLM для использования в узлах.
            use_answer_checker (bool, optional): Включать ли узел проверки ответа. По умолчанию True.
        """
        self.async_llm = async_llm
        self.use_answer_checker = use_answer_checker
        self.prompt_manager = PromptManager()
        self._compiled_graph = None
        self._builder: StateGraph | None = None

    def _build_graph(self) -> StateGraph:
        """Создаёт и конфигурирует StateGraph (внутренний метод)."""
        logger.info("🛠️ Начало построения RAG-графа...")

        logger.info("Инициализация узла DocsCounter...")
        # 🔹 Функция маршрутизации: проверяет, найдены ли документы
        # Возвращает "stop" (END) если документов нет, или "next_step" для продолжения
        router = DocsCounter()

        # ===== УЗЛЫ ОБРАБОТКИ =====
        # Узлы должны возвращать dict для обновления state
        # Если узел не меняет state, он может вернуть пустой dict {}
        llm = BaseLLM(
            llm=self.async_llm,
            prompt=self.prompt_manager.get_prompt("BaseLLM"),
        )

        logger.info("Инициализация узла IntentClassifier...")
        # Узел классификации намерения: анализирует запрос пользователя
        # Возвращает: {"intent": str, ...} (обновляет поле intent в state)
        intent = IntentClassifier(
            llm=self.async_llm,
            prompt=self.prompt_manager.get_prompt("Classifier"),
        )

        logger.info("Инициализация узла RetrieverIntent...")
        # Узел поиска документов: переформулирует запрос и ищет в VectorDB
        # Возвращает: {"retrieved": list[str], ...} (добавляет найденные документы в state)
        retriever = RetrieverIntent(
            llm=self.async_llm,
            prompt=self.prompt_manager.get_prompt("Retriever"),
        )

        logger.info("Инициализация узла Reranker реранкера...")
        # Узел переранжирования: улучшает релевантность документов
        # Возвращает: {"retrieved": list[str], ...} (обновляет documents в state)
        reranker = Reranker()

        ans_check = None
        if self.use_answer_checker:
            logger.info("Инициализация узла проверки ответа (AnswerChecker)")
            # Узел проверки ответа: проверяет качество и релевантность ответа
            ans_check = AnswerChecker(
                llm=self.async_llm,
                prompt=self.prompt_manager.get_prompt("AnswerChecker"),
            )

        logger.info("Сборка графа состояний...")
        builder = StateGraph(RAGState)

        # ===== ДОБАВЛЕНИЕ УЗЛОВ =====
        # Каждый узел должен быть асинхронной функцией (ainvoke)
        # и возвращать dict для обновления RAGState
        builder.add_node("Intent", intent.ainvoke)  # Классификация намерения
        builder.add_node("Retriever", retriever.ainvoke)  # Поиск документов
        # ⚠️ Router НЕ добавляется как узел! Используется только в add_conditional_edges

        builder.add_node("Reranker", reranker.ainvoke)  # Переранжирование документов
        builder.add_node("llm", llm.ainvoke)  # Генерация ответа

        if self.use_answer_checker and ans_check is not None:
            builder.add_node("AnswerChecker", ans_check.ainvoke)  # Проверка ответа

        # ===== ОПРЕДЕЛЕНИЕ РЁБЕР (ПЕРЕХОДОВ) =====
        # add_edge: безусловный переход в следующий узел
        # add_conditional_edges: условный переход в зависимости от функции маршрутизации
        builder.add_edge(START, "Intent")  # Начало → Классификация намерения
        builder.add_edge("Intent", "Retriever")  # Намерение → Поиск документов

        # 🔹 УСЛОВНЫЙ ПЕРЕХОД (Router):
        # router.ainvoke() возвращает:
        #   - "stop" → переход в END (нет документов)
        #   - "next_step" → переход в Reranker (документы найдены)
        builder.add_conditional_edges(
            "Retriever",  # От этого узла
            router.ainvoke,  # Используй эту функцию для принятия решения
            {  # Маршруты (ключ = возвращаемое значение → узел/END)
                "stop": END,  # Нет документов → конец
                "next_step": "Reranker",  # Документы найдены → переранжирование
            },
        )

        builder.add_edge("Reranker", "llm")  # Переранжирование → Генерация ответа

        # ===== ЗАВЕРШЕНИЕ ГРАФА =====
        # Выбор пути в зависимости от использования проверки ответа
        if self.use_answer_checker and ans_check is not None:
            builder.add_edge("llm", "AnswerChecker")  # Ответ → Проверка ответа
            builder.add_edge("AnswerChecker", END)  # Проверка → Конец
            logger.info("✅ Граф построен с узлом AnswerChecker")
        else:
            builder.add_edge("llm", END)  # Ответ → Конец (без проверки)
            logger.info("✅ Граф построен без узла AnswerChecker")

        return builder

    def build(self):
        """Возвращает скомпилированный граф (ленивая инициализация)."""
        if self._compiled_graph is None:
            self._builder = self._build_graph()
            self._compiled_graph = self._builder.compile()
            logger.info("🎉 RAG-граф успешно скомпилирован и готов к использованию")
        return self._compiled_graph

    def get_graph_builder(self) -> StateGraph:
        """Возвращает StateGraph builder для визуализации и отладки."""
        if self._builder is None:
            self._builder = self._build_graph()
        return self._builder

    def get_image_graph(self):
        """Отрисовать граф (использует builder напрямую)."""

        builder = self.get_graph_builder()
        return display(Image(builder.compile().get_graph().draw_mermaid_png()))
