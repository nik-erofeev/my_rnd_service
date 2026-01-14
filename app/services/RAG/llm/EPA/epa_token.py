import asyncio
import time

from app.core.config import EPATokenManagerConfig
from app.core.logger import get_logger
from app.services.RAG.llm.EPA.exceptions import EPATokenError
from app.services.RAG.llm.EPA.schemas import EPAToken
from app.utils.logging_decorators import log_execution_time
from app.utils.post_request import make_request

logger = get_logger(__name__)


class EPATokenManager:
    def __init__(self, config: EPATokenManagerConfig):
        self.login: str = config.login
        self.password: str = config.password
        self.url = config.url
        self.verify = config.verify
        self.__access_token: str | None = None
        self.__expires_in: int | None = None
        self.__lock = asyncio.Lock()

    @property
    async def token(self) -> str:
        """
        Получение id_token с использованием лока.
        Только один вызов может получить id_token одновременно.
        """
        current_time = int(time.time())

        # Если токен ещё действителен — возвращаем его
        if self.__access_token is not None and self.__expires_in is not None and self.__expires_in > current_time:
            return self.__access_token

        async with self.__lock:
            # Если токен истёк или отсутствует — обновляем
            if self.__access_token is None or self.__expires_in is None or self.__expires_in <= current_time:
                logger.info("Getting new EPA token...")
                tokens = await self.get_token()
                self._update_tokens(tokens)

            if self.__access_token is None:
                raise EPATokenError("Не удалось получить токен")

            return self.__access_token

    @property
    async def id_token(self) -> str:
        """Асинхронный метод для получения id_token"""
        return await self.token

    def _update_tokens(self, tokens: EPAToken) -> None:
        """Обновление внутренних токенов"""
        self.__access_token = tokens.access_token
        self.__expires_in = tokens.expires_in + int(time.time())

    @log_execution_time
    async def get_token(self) -> EPAToken:
        """Получения токена"""
        token_request = {
            "grant_type": "client_credentials",
            "client_id": self.login,
            "client_secret": self.password,
        }

        response = await make_request(
            self.url,
            logger=logger,
            payload=token_request,
            verify=self.verify,
            error_class=EPATokenError,
        )
        return EPAToken(**response)
