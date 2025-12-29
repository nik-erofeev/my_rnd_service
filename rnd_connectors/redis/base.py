import json
from abc import ABC, abstractmethod
from datetime import datetime

from rnd_connectors.redis.schemas import RedisConfig


class BaseRedisClient(ABC):
    """Базовый класс Redis клиента, определяющий общий интерфейс"""

    def __init__(self, config: RedisConfig):
        self.expiration = config.expiration
        self._client = None
        self._init_client(config)

    @abstractmethod
    def _init_client(self, config: RedisConfig):
        pass

    @abstractmethod
    def get(self, trace_id: str):
        pass

    @abstractmethod
    def set(self, trace_id: str, data: dict):
        pass

    @staticmethod
    def _prepare_data(data: dict) -> str:
        """Вспомогательная функция для добавления времени и конвертации из dict в str"""
        if "createdAt" not in data:
            data["createdAt"] = datetime.now().isoformat()
        data["updatedAt"] = datetime.now().isoformat()
        return json.dumps(data)


class SyncRedisClient(BaseRedisClient):
    """Синхронный клиент Redis

    Методы синхронного взаимодействия:
    'get', 'set'

    Метод взаимодействия определяется при инициализации класса

    Аттрибуты:
        expiration (int): Время до удаления ключа из базы(в секундах)
        use_async (bool): Переменная, от которой зависит синхронность/асинхронность
        _client (Redis): Клиент Redis (синхронный или асинхронный)"""

    def _init_client(self, config: RedisConfig):
        import redis

        self._client = redis.from_url(config.url, password=config.password)

    def get(self, trace_id: str) -> dict | None:
        """Синхронный get метод"""
        data = self._client.get(trace_id)
        return json.loads(data) if data else None

    def set(self, trace_id: str, data: dict):
        """Синхронный set метод."""
        if not self._client.set(trace_id, self._prepare_data(data), ex=self.expiration):
            raise KeyError("Ключ уже используется")

    def ping(self):
        return self._client.ping()


class AsyncRedisClient(BaseRedisClient):
    """Асинхронный клиент Redis"""

    def _init_client(self, config: RedisConfig):
        import redis.asyncio as redis

        self._client = redis.from_url(config.url, password=config.password)

    async def get(self, trace_id: str) -> dict | None:
        """Асинхронный get метод"""

        data = await self._client.get(trace_id)
        return json.loads(data) if data else None

    async def set(self, trace_id: str, data: dict):
        """Асинхронный set метод."""
        if not await self._client.set(
            trace_id, self._prepare_data(data), ex=self.expiration
        ):
            raise KeyError("Ключ уже используется")

    async def ping(self):
        return await self._client.ping()
