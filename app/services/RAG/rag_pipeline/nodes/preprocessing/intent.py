import logging

from app.services.RAG.exceptions import RagPipelineError
from app.services.RAG.rag_pipeline.nodes.base.base_llm import BaseLLM
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class IntentClassifier(BaseLLM):
    """
    Классифицирует намерения пользователя на основе входящего сообщения.
    """

    async def ainvoke(self, state: RAGState) -> RAGState:
        """Обрабатывает состояние и возвращает классификацию намерения."""
        logger.info("IntentClassifier start wait...")
        # prompt = str(self.prompt.format(**state))
        prompt = str(
            self.prompt.format(
                message=self.process_input_message(state["messages"][-1]),
                history=self.process_input_list(state["messages"][:-1]),
            ),
        )
        try:
            generate_result = await self.llm.generate([{"role": "user", "text": prompt}])
        except RagPipelineError:
            # Уже обработанные - пробрасываем выше
            raise

        response = self.process_output(generate_result)
        logger.info("IntentClassifier end")
        return {"intent": [response]}
