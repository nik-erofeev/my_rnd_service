import logging
import sys
from typing import ClassVar

from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.rag_pipeline.graph.builder import RAGGraphBuilder
from app.services.RAG.rag_pipeline.pipeline import RAGPipeline


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для логов."""

    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET: ClassVar[str] = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        log_color: str = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> logging.Logger:
    """
    Настраивает логирование с цветами и выводом в консоль.

    Устанавливает уровень логирования DEBUG и настраивает кастомный ColoredFormatter
    для более читаемого вывода логов в консоль.

    Returns:
        logging.Logger: Настроенный логгер.
    """
    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)

    # Handler для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Форматтер с цветами и временем
    formatter = ColoredFormatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    return _logger


async def main() -> None:
    """
    Точка входа для запуска примера RAG-пайплайна.

    1. Инициализирует логирование.
    2. Создает асинхронный LLM (AsyncLLM).
    3. Строит граф RAG с помощью RAGGraphBuilder.
    4. Запускает пайплайн с тестовым запросом ("Какой сегодня день?").
    5. Выводит результаты работы пайплайна (ответ, найденные документы, намерения).
    """
    # logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    logger = setup_logging()
    llm = AsyncLLM()
    graph_builder = RAGGraphBuilder(async_llm=llm, use_answer_checker=True)
    rag_pipeline = RAGPipeline(graph=graph_builder.build())

    msg = "Какой сегодня день?"

    rag_result = await rag_pipeline.query(message=msg)

    logger.info(f"Получили ответ от RAG-пайплайна: \n {rag_result}")
    retrieved_docs = rag_result.get("retrieved", [])
    last_message_raw = rag_result["messages"][-1].content if rag_result.get("messages") else None
    last_message = last_message_raw if isinstance(last_message_raw, str) else None

    for doc in retrieved_docs:
        logger.info(f"Документы, которые были найдены по запросу: \n {doc.metadata.get('AdditionalData')}")
        logger.info(f"Содержание документа: \n {doc.page_content}")

    logger.info(f"Последнее сообщение в чате: \n {last_message}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
