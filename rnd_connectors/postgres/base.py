from abc import ABC, abstractmethod

import asyncpg

from rnd_connectors.postgres.schemas import PostgresConfig


class BaseAsyncPostgresClient(ABC):
    def __init__(self, connection_config: PostgresConfig):
        self.connection_config = connection_config
        self.config_dict = self.connection_config.model_dump(
            include={"host", "port", "user", "password", "database"}
        )

    async def check_table_exist(self, table_name: str):
        query = f"""
        SELECT * from {table_name}
        LIMIT 1
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchrow(query)

        except asyncpg.exceptions.UndefinedTableError:
            raise Exception(f"Таблица {table_name} не существует")

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def close(self):
        pass
