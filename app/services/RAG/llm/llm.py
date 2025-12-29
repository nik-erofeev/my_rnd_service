import json
import logging

from ..exceptions import RagPipelineError
from .schemas import AlternativesSchema, MessageSchema, ResponseYAGPTSchema

logger = logging.getLogger(__name__)


class AsyncLLM:
    """Класс для описания асинхронной работы llm"""

    try:

        async def generate(self, prompt: list[dict[str, str]]) -> ResponseYAGPTSchema:
            """Асинхронный метод генерации."""

            # logger.debug(f"с промптом: \n {prompt} \n идем к llm")

            logger.debug(f"Промпт отправляется к LLM:\n{json.dumps(prompt, indent=2, ensure_ascii=False)}")

            example_response = ResponseYAGPTSchema(
                alternatives=[
                    AlternativesSchema(
                        message=MessageSchema(
                            role="assistant",
                            text="Сегодня среда, 17 декабря 2025 года.(тест_мок_ответ)",
                        ),
                        status="ok",
                    ),
                ],
                modelVersion="v1",
            )
            return example_response

    except Exception as e:
        logger.error(f"Ошибка при генерации: {e}")
        raise RagPipelineError(message=f"Ошибка при генерации AsyncLLM: {e}") from e
