from pydantic import BaseModel


class S3Config(BaseModel):
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_name: str

    class ConfigDict:
        env_prefix = "S3_"
