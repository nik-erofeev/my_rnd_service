import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import EPATokenManagerConfig, RNDTokenManagerConfig, RNDYandexConfig, TYKYandexConfig
from app.services.RAG.exceptions import RagPipelineError
from app.services.RAG.llm.EPA.epa_token import EPATokenManager
from app.services.RAG.llm.schemas import AlternativesSchema, MessageSchema, ResponseYAGPTSchema
from app.services.RAG.llm.TYK.exceptions import TYKClientError
from app.services.RAG.llm.TYK.yandex import TYKClient
from app.utils.logging_decorators import log_execution_time
from rnd_connectors.yandex_llm.client import YaGPTAsyncClient
from rnd_connectors.yandex_llm.exceptions import YaGPTClientError
from rnd_connectors.yandex_llm.token_manager import AsyncTokenManager

logger = logging.getLogger(__name__)


class AsyncLLM:
    """
    Универсальный Async генератор:
    - Если TYK включён → используется связка EPA + TYK
    - Если TYK выключен → используется связка TokenManager + YaGPTClient напрямую
    """

    def __init__(
        self,
        epa_token_config: EPATokenManagerConfig,
        tyk_yandex_config: TYKYandexConfig,
        rnd_token_manager_config: RNDTokenManagerConfig,
        rnd_yandex_config: RNDYandexConfig,
        use_tyk: bool,  # True → TYK режим
    ) -> None:
        self.epa_config = epa_token_config
        self.tyk_yandex_config = tyk_yandex_config
        self.rnd_token_manager_config = rnd_token_manager_config
        self.rnd_yandex_config = rnd_yandex_config
        self.use_tyk = use_tyk

        # объявляем общие типы - mypy не понимает, что они разные
        self.token_manager: EPATokenManager | AsyncTokenManager
        self.client: TYKClient | YaGPTAsyncClient

        if self.use_tyk:
            # EPA + TYK
            self.token_manager = EPATokenManager(self.epa_config)
            self.client = TYKClient(config=self.tyk_yandex_config, token_manager=self.token_manager)
            logger.info("AsyncGenerateProcessor initialized in TYK mode")
        else:
            # Прямое подключение к YaGPT через RnD
            self.token_manager = AsyncTokenManager(config=self.rnd_token_manager_config)
            self.client = YaGPTAsyncClient(
                token_manager=self.token_manager,
                folder_id=self.rnd_yandex_config.folder_id,
                api_url=self.rnd_yandex_config.api_url,
                use_ssl=self.rnd_yandex_config.use_ssl,
            )
            logger.info("AsyncGenerateProcessor initialized in Yandex RnD mode")

    # ───────── helpers ─────────
    @property
    def _model_uri(self) -> str:
        """
        Возвращает корректный URI модели.
        При TYK используем TYK-конфиг, иначе RnD-конфиг.
        """
        config = self.tyk_yandex_config if self.use_tyk else self.rnd_yandex_config
        model, folder_id = config.model, config.folder_id

        mapping = {
            "lite": f"gpt://{folder_id}/lite/latest",
            "lite:latest": f"gpt://{folder_id}/lite/latest",
            "lite:deprecated": f"gpt://{folder_id}/lite/deprecated",
            "lite:rc": f"gpt://{folder_id}/lite/rc",
            "pro": f"gpt://{folder_id}/pro-ws-2/latest",
            "pro:latest": f"gpt://{folder_id}/pro-ws-2/latest",
            "pro:deprecated": f"gpt://{folder_id}/pro-ws-2/deprecated",
            "pro:rc": f"gpt://{folder_id}/pro-ws-2/rc",
            "query_emb": f"emb://{folder_id}/text-search-query/rc",
            "doc_emb": f"emb://{folder_id}/text-search-doc/rc",
        }

        if model not in mapping:
            raise ValueError(f"Unknown model type: {model}")
        return mapping[model]

    # ───────── main ─────────
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=5),
        retry=retry_if_exception_type(RagPipelineError),
        reraise=True,
    )
    async def generate(self, prompt: list[dict[str, str]]) -> ResponseYAGPTSchema:
        """
        Основной метод генерации текста.

        :param prompt: список сообщений (chat history)
        :return: объект ResponseYAGPTSchema с результатом
        """
        config = self.tyk_yandex_config if self.use_tyk else self.rnd_yandex_config

        payload: dict[str, Any] = {
            "modelUri": self._model_uri,
            "messages": prompt,
            "completionOptions": {
                "stream": False,
                "temperature": config.temperature,
                "maxTokens": config.max_tokens,
            },
        }

        try:
            if self.use_tyk:
                raw = await self._generate_via_tyk(payload)
            else:
                raw = await self._generate_via_yandex(payload)

        except (TYKClientError, YaGPTClientError) as e:
            logger.exception("Ошибка при вызове LLM API (%s)", "TYK" if self.use_tyk else "Yandex RnD")
            raise RagPipelineError(
                message=f"Ошибка LLM API: {e}",
            ) from e

        except Exception as e:
            logger.exception("Неизвестная ошибка при обращении к LLM API")
            raise RagPipelineError(
                message=f"Неизвестная ошибка LLM: {e!r}",
            ) from e

        # ───────── парсинг ─────────
        try:
            result = raw.get("result", raw) if isinstance(raw, dict) else raw
            return ResponseYAGPTSchema(**result)
        except Exception as parse_error:
            logger.exception("Ошибка парсинга ответа LLM")
            raise RagPipelineError(
                message=f"Ошибка парсинга ответа: {parse_error!r}; raw={raw}",
            ) from parse_error

    @log_execution_time
    async def _generate_via_tyk(self, payload: dict[str, Any]) -> dict[str, Any]:
        client: TYKClient = self.client  # type: ignore
        return await client.completion(payload)

    @log_execution_time
    async def _generate_via_yandex(self, payload: dict[str, Any]) -> dict[str, Any]:
        client: YaGPTAsyncClient = self.client  # type: ignore
        return await client.post(endpoint="completion", payload=payload)


# ───────── локальный фолбэк ─────────
class LocalAsyncYandexLLM:

    def __init__(
        self,
        api_key: str,
        folder_id: str,
        model: str,
        url: str,
    ):
        self._api_key = api_key
        self._folder_id = folder_id
        self.model = model
        self.url = url.rstrip()

    # Конфигурация ретраев
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=5),
        retry=retry_if_exception_type(RagPipelineError),
        reraise=True,
    )
    async def generate(self, prompt: list[dict[str, str]]) -> ResponseYAGPTSchema:
        payload = {
            "modelUri": f"gpt://{self._folder_id}/{self.model}",
            "messages": prompt,
            "completionOptions": {
                "stream": False,
                "temperature": 0.82,
                "maxTokens": 2000,
            },
        }

        headers = {"Authorization": f"Api-Key {self._api_key}"}

        start_time = datetime.now()
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            try:
                resp = await client.post(self.url, headers=headers, json=payload)
            except Exception as e:
                raise RagPipelineError(
                    message=f"Ошибка обработки сообщения к Yandex Llm: {e!r}",
                ) from e

        logger.info(
            f"Время выполнения LocalYandexGPT.generate = {(datetime.now() - start_time).total_seconds()} секунд",
        )

        if resp.status_code != httpx.codes.OK:
            raise RagPipelineError(
                message=f"Ошибка обработки сообщения к Yandex Llm: {resp.status_code}: {resp.text}",
            )

        resp_json = resp.json()
        return ResponseYAGPTSchema(**resp_json["result"])


class LocalAsyncOllamaLLM:
    """
    Ollama LLM — полностью совместим с интерфейсом LocalAsyncYandexLLM.

    Использует HTTP API Ollama напрямую через httpx (как у Yandex).
    Работает с HumanMessage из RAGPipeline и возвращает ResponseYAGPTSchema.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        temperature: float = 0.82,
        max_tokens: int = 2000,
    ):
        """
        Инициализация Ollama LLM.

        Args:
            model: Название модели (например, "mistral", "llama3.2:3b")
            base_url: URL Ollama сервера (по умолчанию localhost)
            temperature: Температура генерации (0-1)
            max_tokens: Максимальное количество токенов в ответе
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.url = f"{self.base_url}/api/chat"  # Ollama chat endpoint

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=5),
        retry=retry_if_exception_type(RagPipelineError),
        reraise=True,
    )
    async def generate(self, prompt: list[dict[str, str]]) -> ResponseYAGPTSchema:
        """
        Генерирует ответ от Ollama.

        Args:
            prompt: Список сообщений [{"role": "user", "text": "..."}]

        Returns:
            ResponseYAGPTSchema с альтернативами ответов

        Raises:
            RagPipelineError при ошибке подключения или парсинга
        """
        # Конвертируем формат: {"text": ...} → {"content": ...}
        messages = [{"role": m["role"], "content": m["text"]} for m in prompt]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,  # Ollama использует num_predict
            },
        }

        start_time = datetime.now()
        async with httpx.AsyncClient(verify=False, timeout=60) as client:
            try:
                resp = await client.post(self.url, json=payload)
            except Exception as e:
                raise RagPipelineError(
                    message=f"Ошибка обработки сообщения к Ollama: {e!r}",
                ) from e

        logger.info(
            f"Время выполнения LocalAsyncOllamaLLM.generate = {(datetime.now() - start_time).total_seconds():.3f} секунд",
        )

        if resp.status_code != httpx.codes.OK:
            raise RagPipelineError(
                message=f"Ошибка обработки сообщения к Ollama: {resp.status_code}: {resp.text}",
            )

        resp_json = resp.json()

        # Парсим ответ Ollama
        try:
            content = resp_json["message"]["content"]
            response_model = resp_json["model"]
        except KeyError as e:
            raise RagPipelineError(
                message=f"Некорректный формат ответа от Ollama: {e!r}, resp={resp_json}",
            ) from e

        # Формируем ResponseYAGPTSchema совместимо с твоим schema
        return ResponseYAGPTSchema(
            alternatives=[
                AlternativesSchema(
                    message=MessageSchema(role="assistant", text=content),
                    status="ok",
                ),
            ],
            modelVersion=response_model,
        )
