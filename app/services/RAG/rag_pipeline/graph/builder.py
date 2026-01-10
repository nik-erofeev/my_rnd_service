import logging

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

    def build(self):
        """Собирает и компилирует граф состояний.


        Returns:
            Скомпилированный исполняемый граф.
        """
        logger.info("🛠️ Начало построения RAG-графа...")

        logger.info("Инициализация узла DocsCounter...")
        # 🔹 Узел маршрутизации по числу найденных документов
        router = DocsCounter()

        # Узлы пайплайна
        llm = BaseLLM(
            llm=self.async_llm,
            prompt=self.prompt_manager.get_prompt("BaseLLM"),
        )

        logger.info("Инициализация узла IntentClassifier...")
        intent = IntentClassifier(
            llm=self.async_llm,
            prompt=self.prompt_manager.get_prompt("Classifier"),
        )

        logger.info("Инициализация узла RetrieverIntent...")
        retriever = RetrieverIntent(
            llm=self.async_llm,
            prompt=self.prompt_manager.get_prompt("Retriever"),
        )

        logger.info("Инициализация узла Reranker реранкера...")
        reranker = Reranker()

        ans_check = None
        if self.use_answer_checker:
            logger.info("Инициализация узла проверки ответа (AnswerChecker)")
            ans_check = AnswerChecker(
                llm=self.async_llm,
                prompt=self.prompt_manager.get_prompt("AnswerChecker"),
            )

        logger.info("Сборка графа состояний...")
        builder = StateGraph(RAGState)

        # Добавление узлов
        builder.add_node("Intent", intent.ainvoke)  # intent
        builder.add_node("Retriever", retriever.ainvoke)
        builder.add_node("Router", router.ainvoke)
        builder.add_node("Reranker", reranker.ainvoke)
        builder.add_node("llm", llm.ainvoke)

        if self.use_answer_checker and ans_check is not None:
            builder.add_node("AnswerChecker", ans_check.ainvoke)

        # 🔹 Структура графа
        builder.add_edge(START, "Intent")
        builder.add_edge("Intent", "Retriever")

        # 🔹 Маршрутизатор: если документов нет — стоп, если есть — продолжаем
        builder.add_conditional_edges(
            "Retriever",
            router.ainvoke,
            {
                "stop": END,
                "next_step": "Reranker",
            },
        )

        builder.add_edge("Reranker", "llm")

        # Завершение графа
        if self.use_answer_checker and ans_check is not None:
            builder.add_edge("llm", "AnswerChecker")
            builder.add_edge("AnswerChecker", END)
            # builder.add_edge("irrelevant_input", END)  # irrelevant_input тоже ведет в END
            logger.info("✅ Граф построен с узлом AnswerChecker")
        else:
            builder.add_edge("llm", END)
            # builder.add_edge("irrelevant_input", END)  # irrelevant_input тоже ведет в END
            logger.info("✅ Граф построен без узла AnswerChecker")

        compiled_graph = builder.compile()
        logger.info("🎉 RAG-граф успешно скомпилирован и готов к использованию")
        return compiled_graph

    def get_image_graph(self):
        """
        Отрисовать график
        """
        from IPython.display import Image, display

        graph = self.build()
        return display(Image(graph.get_graph().draw_mermaid_png()))
