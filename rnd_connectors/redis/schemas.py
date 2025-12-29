from pydantic import BaseModel


class RedisConfig(BaseModel):
    url: str
    expiration: int
    password: str
    use_async: bool = False

    class ConfigDict:
        env_prefix = "REDIS_"
