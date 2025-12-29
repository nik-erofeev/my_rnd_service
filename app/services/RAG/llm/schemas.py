from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    role: str = Field(..., description="Роль отправителя (assistant)")
    text: str = Field(..., description="Текс сообщения")


class AlternativesSchema(BaseModel):
    message: MessageSchema
    status: str = Field(..., description="Статус альтернативы")


class ResponseYAGPTSchema(BaseModel):
    alternatives: list[AlternativesSchema]
    modelVersion: str = Field(..., description="Версия модели")
