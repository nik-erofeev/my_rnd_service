import logging
from typing import Any

from app.services.RAG.exceptions import RagPipelineError
from app.services.RAG.rag_pipeline.nodes.base.base_llm import BaseLLM
from app.services.RAG.rag_pipeline.state import RAGState

logger = logging.getLogger(__name__)


class AnswerChecker(BaseLLM):
    """
    Проверяет качество и релевантность ответа ИИ.
    """

    @staticmethod
    def check_message(message_list: list[Any], m_type: str = "human") -> list[Any]:
        """
        Фильтрует сообщения по типу (human/ai).

        Args:
            message_list: Список сообщений для фильтрации.
            m_type (str): Тип сообщения для отбора ('human' или 'ai').

        Returns:
            list: Список отобранных сообщений.
        """
        return [m for m in message_list if (m.type == m_type)]

    async def ainvoke(self, state: RAGState) -> RAGState:
        """
        Проверяет ответ ИИ на соответствие вопросу и контексту.

        Использует LLM для оценки качества ответа. Если ответ нерелевантен, возвращает '0'.

        Args:
            state (RAGState): Текущее состояние графа.

        Returns:
            RAGState: Обновленное состояние с результатом проверки (или исходным ответом).
        """
        logger.info("AnswerChecker generate start")
        # self.time_sleep()
        # prompt = str(self.prompt.format(**state))
        prompt = str(
            self.prompt.format(
                answer=self.process_input_message(
                    self.check_message(
                        message_list=state["messages"],
                        m_type="ai",
                    )[-1],
                ),
                message=self.process_input_message(
                    self.check_message(
                        message_list=state["messages"],
                        m_type="human",
                    )[-1],
                ),
                context=state["retrieved"],
            ),
        )
        try:
            generate_result = await self.llm.generate([{"role": "user", "text": prompt}])
        except RagPipelineError:
            # Уже обработанные ошибки - просто пробрасываем
            raise

        response = self.process_output(generate_result)
        logger.info("AnswerChecker generate end")
        return {"messages": [response]}
