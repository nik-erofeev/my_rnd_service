from pydantic import BaseModel


class PostgresConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str

    class ConfigDict:
        env_prefix = "POSTGRES_"
