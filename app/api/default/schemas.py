from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    service: str


class ExcResponse(BaseModel):
    message: str
