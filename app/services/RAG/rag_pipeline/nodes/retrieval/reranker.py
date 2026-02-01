import logging

from app.services.RAG.rag_pipeline.exceptions import RagPipelineError
from app.services.RAG.rag_pipeline.nodes.base.base_node import BaseNode
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class Reranker(BaseNode):
    """Классический реренкер для ранжирования документов по оценке релевантности.

    Использует BentoML сервис для вычисления скоров релевантности
    и возвращает топ-N наиболее релевантных документов.
    """

    def __init__(self, n_best: int = 5):
        """Инициализация классического реренкера.

        Args:
            n_best: Количество лучших документов для возврата
        """
        super().__init__()
        self.n_best = n_best

    async def ainvoke(self, state: RAGState) -> RAGState:
        """
        Выполняет реранкинг документов.

        Принимает текущее состояние RAG, извлекает найденные документы (retrieved),
        и (в перспективе) переупорядочивает их по релевантности.

        Args:
            state (RAGState): Текущее состояние пайплайна.

        Returns:
            Состояние с переранжированными документами
        """
        try:
            logger.info("Reranker start wait...")

            # достаем чанки/документы
            chunks = state["retrieved"]

            # с помощью реранкера ранжируем документы (какая-то логика)
            ranked_docs = chunks

            logger.info(f"✅ Reranker завершен, возвращено " f"{len(ranked_docs)} чанков(а)")
            return {"retrieved": ranked_docs}

        except RagPipelineError:
            # Пробрасываем уже известные ошибки
            raise
        except Exception as e:
            logger.error(f"Ошибка при вызове BentoMLReranker. Ошибка = {e}.")
            raise RagPipelineError(message=f"Ошибка реранкинга документов: {e!r}") from e
