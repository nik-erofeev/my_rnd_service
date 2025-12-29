from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

"""
You can read more about it.
Link to Confluence.
https://wiki.corp.dev.vtb/pages/viewpage.action?pageId=1666062016
"""


class ErrorType(str, Enum):
    SYSTEM = "System"
    BUSINESS = "Business"


class FluentError(BaseModel):
    """
    This data class describes the entity of the fluentd adapter error.
    """

    errorCode: str = Field(default="0", description="Код ошибки")
    errorType: ErrorType | None = Field(default=None, description="Тип ошибки")
    errorString: str = Field(default="No errors", description="Описание ошибки/успеха")

    model_config = ConfigDict(use_enum_values=True)


class StagesKafkaMessages(BaseModel):
    inReceived: float | None = Field(
        default=None,
        description="Когда взяли сообщение из кафки в обработку",
    )
    inValidated: float | None = Field(
        default=None,
        description="Когда успешно его провалидировали",
    )
    inTransformed: float | None = Field(
        default=None,
        description="Когда успешно его трансформировали в формат модели",
    )
    inSent: float | None = Field(default=None, description="Когда вызвали сервис модели")
    outReceived: float | None = Field(default=None, description="Когда получили ответ от модели")
    outValidated: float | None = Field(
        default=None,
        description="Когда успешно его провалидировали",
    )
    outTransfromed: float | None = Field(
        default=None,
        description="Когда успешно его трансформировали в формат потребителя",
    )
    outSent: float | None = Field(default=None, description="Когда положили ответ в кафку")


class FluentExt(BaseModel):
    """
    This data class describes the entity of the additional information
    of the fluentd adapter about the deployment environment.
    """

    serviceNamespace: str | None = Field(
        default=None,
        description="Адрес kubernetes (пример 'dev-test')",
    )
    serviceName: str | None = Field(
        default=None,
        description="Название сервиса в kubernetes (пример 'rkk-sas-mock')",
    )
    openshiftName: str | None = Field(
        default=None,
        description="имя&nbsp;Kubernetes (пример 'rs1-gen01.test.vtb.ru')",
    )
    imageVersion: str | None = Field(
        default=None,
        description="Название образа (пример '0.0.1-snap')",
    )
    endpoint: str | None = Field(default=None, description="endpoint модели")
    errorStackTrace: str | None = Field(default=None, description="стектрейс)")
    stages: StagesKafkaMessages | None = None


class FluentMessage(BaseModel):
    """
    This data class describes the entity of the fluentd adapter message.
    """

    action: str | None = Field(
        default=None,
        description="Наименование текущей, атомарной операции (например task name в Airflow)",
    )
    actionId: str | None = Field(default=None, description="ID атомарной операции")
    system: str | None = Field(
        default=None,
        description="Код ИС/Подсистемы из РИС (пример 1655_1)",
    )
    message: str | None = Field(
        default=None,
        description="отметка о состоянии атомарной операции {Started | Complete | Failed}",
    )
    environment: str | None = Field(default=None, description="окружение (Test/preprod/prod)")
    node: str | None = Field(default=None, description="Id машины")
    errors: list[FluentError] = Field(default_factory=list)
    ext: FluentExt | None = None


class FluentEvent(BaseModel):
    """
    This data class describes the entity of the fluentd adapter event.
    """

    severity: str = Field(description="log level (INFO, WARNING, ERROR, CRITICAL)")
    message: FluentMessage


class FluentELKLog(BaseModel):
    """
    This data class describes the entity of the fluentd adapter log.
    """

    index: str = Field(description="название индекса, куда попадет лог(1655_1__service_name)")
    sourceType: str | None = Field(default=None, description="Airflow/is3")
    timestamp: str = Field(description="Время записи события (Unix timestamp)")
    time: int = Field(description="Время записи события (Unix timestamp)")
    rqId: str | None = Field(
        default=None,
        description="Идентификатор запроса, берется из входящего сообщения",
    )
    event: FluentEvent


class FluentDBLog(BaseModel):
    source_name: str
    request_id: str | None = Field(
        default=None,
        description="Идентификатор запроса, берется из входящего сообщения",
    )
    log_level: str | None = Field(
        default=None,
        description="log level (INFO, WARNING, ERROR, CRITICAL)",
    )
    logger_name: str | None = Field(
        default=None,
        description="имя сообщения или логгера",
        max_length=200,
    )
    host_name: str | None = Field(default=None, description="хост сервера", max_length=200)
    thread_name: str | None = Field(default=None, max_length=200)
    message: str
    event_date: str


class FluentZSMLog(BaseModel):
    timestamp: str = Field(default_factory=lambda: str(datetime.now(timezone.utc).timestamp()))
    ris_code: str = Field(description="код РИС без подсистемы")
    subsystem_code: str = Field(description="Номер подсистемы (0 если нет)")
    metric_name: str
    metric_value: float
    config_item: str = Field(
        description="имя КЕ, используется для привязки метрик к карточке мониторинга ЗСМ. КЕ должна присутствовать в CDMB Банка и быть добавлена в карточку мониторинга ИС",  # noqa: E501
    )
    labels: dict = Field(description="массив меток")
    lableIN: dict | None = Field(
        default=None,
        description="доп метрики (имя без пробелов, значение-текст)",
    )
