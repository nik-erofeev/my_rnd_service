from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field


class ConsumerMessage(BaseModel):
    """
    Входящее сообщение для воркера.
    """

    ...


class ProducerMessage(BaseModel):
    """
    Исходящее сообщение для воркера.
    """

    ...


class LangchainConsumerMessage(BaseModel):
    """
    Входящее сообщение для воркера.
    """

    test_questions: str = Field(..., description="Входящее сообщение в топик in")


class CodeError(IntEnum):
    UNEXPECTED_ERROR = 1
    MESSAGE_VALIDATION_ERROR = 2


ERROR_TRACES = {
    1: "Непредвиденная ошибка",
    2: "Ошибка валидации входящего сообщения",
}


class StatusCode(IntEnum):
    SUCCESS = 100  # успешные
    PROCESSING_ERROR = 400  # не успешные


class ErrorInfo(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codeError: CodeError = Field(description="код ошибки")
    trace: str = Field(
        description="log с описанем ошибки",
    )
    message: str | None = Field(
        None,
        description="Детальное сообщение об ошибке (опционально)",
    )


class LangchainProducerMessage(ProducerMessage):
    message: str = Field(..., description="Сообщение в топит out")
    statusCode: StatusCode = Field(description="код статуса. 100 - успешно. >101 - ошибка")
    errorInfo: list[ErrorInfo] | None = Field(default=None, description="Информация об ошибке")


class HeadersTopikIn(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    requestId: str = Field(description="id сообщения")


class HeadersTopikOut(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    requestId: str = Field(description="id сообщения")
