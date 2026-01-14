import logging

from app.core.config import CONFIG
from app.core.container import DependencyContainer
from app.core.logger import setup_logger


async def main(msg: str) -> None:
    """
    Точка входа для запуска примера RAG-пайплайна.

    1. Инициализирует логирование.
    2. Создает контейнер
    3. инициализируем контейнер
    4. Запускает пайплайн с тестовым запросом.
    5. Выводит результаты работы пайплайна (ответ, найденные документы, намерения).
    """
    setup_logger(CONFIG)

    logger = logging.getLogger(__name__)

    container = DependencyContainer(config=CONFIG)

    try:
        # прогреваем всё (опционально)
        await container.init_async()
        rag_pipeline = container.pipeline

        rag_result = await rag_pipeline.query(message=msg)

        logger.info(f"Получили ответ от RAG-пайплайна: \n {rag_result}")
        retrieved_docs = rag_result.get("retrieved", [])
        last_message_raw = rag_result["messages"][-1].content if rag_result.get("messages") else None
        last_message = last_message_raw if isinstance(last_message_raw, str) else None

        for doc in retrieved_docs:
            logger.info(f"Документы, которые были найдены по запросу: \n {doc.metadata.get('AdditionalData')}")
            logger.info(f"Содержание документа: \n {doc.page_content}")

        logger.info(f"Последнее сообщение в чате: \n {last_message}")
    finally:
        await container.aclose()


if __name__ == "__main__":
    import asyncio

    # msg = "Какой сегодня день?"
    msg = "Какие документы нужны для оформления ипотеки?"
    # msg = "Функции и ответственность коллегиальных органов в рамках, процесса управления Риском аутсорсинга"
    asyncio.run(main(msg))
