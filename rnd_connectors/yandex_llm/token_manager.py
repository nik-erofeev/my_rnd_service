import asyncio
import logging
import threading
import time
from typing import Optional

import httpx

from rnd_connectors.yandex_llm.exceptions import YaGPTClientError
from rnd_connectors.yandex_llm.protocols import TokenManagerConfigProtocol
from rnd_connectors.yandex_llm.schemas import Tokens

logger = logging.getLogger(__name__)


class BaseTokenManager:
    def __init__(self, config: TokenManagerConfigProtocol):
        self.login: str = config.login
        self.password: str = config.password
        self.url: str = config.url
        self.verify: bool = config.verify
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._id_token: str | None = None
        self._expires_in: int | None = None

    def _update_tokens(self, tokens: Tokens) -> None:
        """Обновление внутренних токенов"""
        self._access_token = tokens.access_token
        self._refresh_token = tokens.refresh_token
        self._id_token = tokens.id_token
        self._expires_in = tokens.expires_in + int(time.time())

    @staticmethod
    def _create_headers():
        return {
            "Content-Type": "application/json; charset=utf-8",
        }

    def _create_body(self):
        return {
            "login": self.login,
            "password": self.password,
        }


class SyncTokenManager(BaseTokenManager):
    """Синхронный менеджер токенов"""

    def __init__(
        self,
        config: TokenManagerConfigProtocol,
        lock: Optional[threading.Lock] = None,
    ):
        super().__init__(config)
        self._lock = lock if lock is not None else threading.Lock()

    @property
    def id_token(self) -> str:
        """Cинхронный метод для получения id_token"""
        return self._get_id_token()

    def _get_id_token(self) -> str:
        with self._lock:
            current_time = int(time.time())
            if (
                self._id_token is None
                or self._expires_in is None
                or self._expires_in <= current_time
            ):
                tokens = self._get_tokens()
                self._update_tokens(tokens)
            if self._id_token is None or self._refresh_token is None:
                raise ValueError("ID token is not available")
            return self._id_token

    def _get_tokens(self) -> Tokens:
        """Cинхронный метод для получения токена"""
        header_token = self._create_headers()
        token_request = self._create_body()

        with httpx.Client(verify=self.verify) as client:
            response = client.post(
                self.url,
                headers=header_token,
                json=token_request,
            )
            if response.status_code != 200:
                raise YaGPTClientError(response.text)

            response_data = response.json()
            logger.info("Tokens successfully obtained")

        return Tokens(**response_data)


class AsyncTokenManager(BaseTokenManager):
    """Асинхронный менеджер токенов"""

    def __init__(self, config: TokenManagerConfigProtocol, lock: asyncio.Lock | None = None):
        super().__init__(config)
        self._lock = lock if lock is not None else asyncio.Lock()

    @property
    async def id_token(self) -> str:
        """Асинхронный метод для получения id_token"""
        return await self._get_id_token()

    async def _get_id_token(self) -> str:
        """Асинхронный метод для получения id_token (с использованием асинхронного лока)"""
        async with self._lock:
            current_time = int(time.time())
            if (
                self._id_token is None
                or self._expires_in is None
                or self._expires_in <= current_time
            ):
                tokens = await self._get_tokens()
                self._update_tokens(tokens)

            if self._id_token is None or self._refresh_token is None:
                raise ValueError("ID token is not available")

            return self._id_token

    async def _get_tokens(self) -> Tokens:
        """Асинхронный метод для получения токена"""
        header_token = self._create_headers()
        token_request = self._create_body()

        async with httpx.AsyncClient(verify=self.verify) as client:
            response = await client.post(
                self.url,
                headers=header_token,
                json=token_request,
            )
            if response.status_code != 200:
                raise YaGPTClientError(response.text)

            response_data = response.json()
            logger.info("Tokens successfully obtained")

        return Tokens(**response_data)
