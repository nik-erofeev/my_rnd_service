from __future__ import annotations

import logging
from typing import Any, Literal
from urllib.parse import urljoin

import httpx

from rnd_connectors.yandex_llm.exceptions import YaGPTClientError
from rnd_connectors.yandex_llm.token_manager import AsyncTokenManager, SyncTokenManager

logger = logging.getLogger(__name__)

# ───────────────────────── internal helpers ─────────────────────────
_HTTP_METHOD = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class HeaderMixin:
    def __init__(self, folder_id: str):
        self.folder_id: str = folder_id

    def create_headers(self, token: str, *extra: dict[str, str] | None) -> dict[str, str]:
        """
        Формирует заголовки для запроса.
        :param token: строка токена авторизации
        :param extra: любое количество dict-ов с дополнительными заголовками
        :return: итоговый dict заголовков
        """
        headers: dict[str, str] = {
            "Authorization": token,
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json",
        }
        for hdr in extra:
            if hdr:
                headers.update(hdr)
        return headers


# ─────────────────────────── Sync client ─────────────────────────────
class YaGPTSyncClient(HeaderMixin):
    def __init__(
        self,
        token_manager: SyncTokenManager,
        folder_id: str,
        api_url: str,
        use_ssl: bool = False,
    ):
        super().__init__(folder_id=folder_id)
        self.token_manager = token_manager
        self.api_url = api_url
        self.use_ssl = use_ssl

    def _full_url(self, endpoint: str) -> str:
        return urljoin(self.api_url, endpoint)

    def _create_headers(self, *extra: dict[str, str] | None) -> dict[str, str]:
        return self.create_headers(self.token_manager.id_token, *extra)

    def request(
        self,
        method: _HTTP_METHOD,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        merged_headers = self._create_headers(headers)

        try:
            with httpx.Client(verify=self.use_ssl, timeout=timeout) as client:
                response = client.request(
                    method=method,
                    url=self._full_url(endpoint),
                    json=json,
                    headers=merged_headers,
                )
            if response.status_code != 200:
                raise YaGPTClientError(response.text)
            return response.json()

        except httpx.ReadTimeout:
            logger.exception("Sync YaGPT %s %s failed", method, endpoint)
            raise YaGPTClientError("Истекло время ожидания read_timeout")

        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.exception("Sync YaGPT %s %s failed: %s", method, endpoint, exc)
            raise YaGPTClientError(str(exc)) from exc

    # wrapper – keeps legacy call-site unchanged
    def post(
        self,
        endpoint: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        """
        Выполняет синхронный POST-запрос к YaGPT API.
        """
        return self.request("POST", endpoint, json=payload, headers=headers, timeout=timeout)


# ──────────────────────────── Async client ───────────────────────────


class YaGPTAsyncClient(HeaderMixin):
    """
    Main client used by Pipeline / Processors.

    • stream & reasoning_mode – deliberately disabled (False / None)
    • any HTTP verb supported via `request`
    """

    def __init__(
        self,
        token_manager: AsyncTokenManager,
        folder_id: str,
        api_url: str,
        use_ssl: bool = False,
    ):
        super().__init__(folder_id=folder_id)
        self.token_manager = token_manager
        self.api_url = api_url
        self.use_ssl = use_ssl

    def _full_url(self, endpoint: str) -> str:
        return urljoin(self.api_url, endpoint)

    async def _create_headers(self, *extra: dict[str, str] | None) -> dict[str, str]:
        return self.create_headers(await self.token_manager.id_token, *extra)

    async def request(  # noqa: D401
        self,
        method: _HTTP_METHOD,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(verify=self.use_ssl, timeout=timeout) as client:
                merged_headers = await self._create_headers(headers)
                response = await client.request(
                    method=method,
                    url=self._full_url(endpoint),
                    json=json,
                    headers=merged_headers,
                )
            if response.status_code != 200:
                raise YaGPTClientError(response.text)
            return response.json()

        except httpx.ReadTimeout:
            logger.exception("Async YaGPT %s %s failed", method, endpoint)
            raise YaGPTClientError("Истекло время ожидания read_timeout")

        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.exception("Async YaGPT %s %s failed: %s", method, endpoint, exc)
            raise YaGPTClientError(str(exc)) from exc

    # convenience wrapper (keeps old API)
    async def post(
        self,
        endpoint: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        """
        Выполняет асинхронный POST-запрос к YaGPT API.
        """
        return await self.request(
            "POST",
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
