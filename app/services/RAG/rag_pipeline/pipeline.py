import logging
from random import randint

import torch
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from app.services.RAG.exceptions import RagPipelineError
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Фасад для полного RAG-пайплайна: от данных до ответа."""

    def __init__(
        self,
        graph,
    ):
        """
        Инициализация RAG-пайплайна.
        """

        self.graph = graph

    async def query(
        self,
        message: str,
        callbacks=None,
    ) -> RAGState:
        """Выполняет RAG-запрос по входному сообщению."""
        try:
            config = RunnableConfig(
                configurable={"request_id": randint(1, 100)},
                callbacks=callbacks or [],
            )
            with torch.no_grad():
                result: RAGState = await self.graph.ainvoke(
                    {
                        "messages": [HumanMessage(content=str(message))],
                        "intent": [],
                        "retrieved": [],
                    },
                    config=config,
                )
                return result
        except RagPipelineError:
            # Уже обработанные - пробрасываем выше
            raise

        except Exception as e:
            logger.exception(f"Ошибка в RAG-пайплайне при обработке запроса: {message}")

            raise RagPipelineError(
                message=f"Ошибка обработки запроса в RAG-пайплайне: {e!r}",
            ) from e
