from httpx import AsyncClient, HTTPStatusError, ReadTimeout, RequestError, codes

from app.core.config import TYKYandexConfig
from app.core.logger import get_logger
from app.services.RAG.llm.EPA.epa_token import EPATokenManager
from app.services.RAG.llm.TYK.exceptions import TYKClientError
from app.utils.logging_decorators import log_execution_time

logger = get_logger(__name__)


class TYKClient:
    """
    Асинхронный клиент для запросов к YandexGPT через TYK Gateway.
    Использует EPA токен, полученный через EPATokenManager.
    """

    def __init__(self, config: TYKYandexConfig, token_manager: EPATokenManager) -> None:
        self.config: TYKYandexConfig = config
        self.token_manager: EPATokenManager = token_manager

    @log_execution_time
    async def completion(self, payload: dict):
        """
        Делает POST-запрос к TYK API с валидным EPA токеном.
        Возвращает JSON-ответ как dict[str, Any].
        """
        token = await self.token_manager.token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with AsyncClient(verify=False, timeout=30) as client:
                response = await client.post(self.config.api_url, json=payload, headers=headers)

            if response.status_code != codes.OK:
                raise TYKClientError(
                    f"TYK API returned {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

        except ReadTimeout as exc:
            logger.exception("TYK request timeout")
            raise TYKClientError("TYK request timeout") from exc

        except (RequestError, HTTPStatusError) as exc:
            logger.exception("TYK request failed: %s", exc)
            raise TYKClientError(str(exc)) from exc
