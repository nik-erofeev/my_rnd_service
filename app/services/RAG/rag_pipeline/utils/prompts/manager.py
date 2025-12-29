import logging

from app.services.RAG.rag_pipeline.utils.prompts.prompts import all_prompts

logger = logging.getLogger(__name__)


class PromptManager:
    """Простой менеджер для управления промптами системы."""

    def __init__(self, prompts_dict: dict[str, list[str]] = all_prompts):
        """
        Args:
            prompts_dict: Словарь с промптами {имя: [список_шаблонов]}
        """
        self.prompts = prompts_dict
        logger.debug(f"Загружены промпты: {list(self.prompts.keys())}")

    def get_prompt(self, name: str) -> str:
        """Возвращает первый промпт из списка по имени.

        Args:
            name: Имя промпта

        Returns:
            Строка промпта

        Raises:
            KeyError: Если промпт не найден
        """
        if name not in self.prompts:
            raise KeyError(f"Промпт '{name}' не найден. Доступные: {list(self.prompts.keys())}")

        if not self.prompts[name]:
            raise ValueError(f"Промпт '{name}' пустой")

        return self.prompts[name][0]
