from pydantic import BaseModel, Field


class TSLGMsgSchemas(BaseModel):
    """Схема параметров для отправки в агента."""

    appName: str = Field(..., description="Название приложения - python_online_rag_3287_shturman_1")
    appType: str = Field(..., description="Тип приложения - (PYTHON/JAVA/NODEJS/GO)")
    envType: int | str = Field(..., description="Тип окружения K8S | VM | FAAS ...")
    risCode: str = Field(..., description="Номер информационной системы/подсистемы - 1655_21")
    projectCode: str = Field(
        ...,
        description="Идентификационный Код Системы/подсистемы "
        "(из Реестра Информационных Систем) - SDO, ELS, TSLG...",
    )

    level: str = Field(..., description="Уровень критичности TRACE, DEBUG, INFO, WARN, ERROR...")
    text: str = Field(
        ...,
        description="Текст события. Неструктурированная дополнительная информация, "
        "необходимая для анализа логов и представленная в текстовом виде",
    )

    # Расширения для логов ПИТОН приложения
    callerMethod: str = Field(
        ...,
        description="пример значения - logging.debug = '{record.filename}.{record.funcName}'}",
    )
    callerLine: int | None = Field(default=None, description="Номер вызываемой строки")
    PID: int | None = Field(description="Номер процесса", default=None)
    stack: str | None = Field(description="Текст ошибки - exc_info", default=None)
    threadName: str | None = Field(default=None)
    loggerName: str | None = Field(default=None)

    eventId: str = Field(..., description="Идентификатор в сообщении (uuid или hash код от сообщения)")
    localTime: str = Field(..., description="Момент времени логирования формат ISO 8601")

    # Поля, формирующиеся в логах k8s/агентом
    podName: str | None = Field(default=None)
    hostName: str = Field(...)
    tec: dict[str, str | None] | str = Field(
        ...,
        description="tec(Технический код) формируется как " '"{podIp}": podIp, "nodeName":"d1cube-cn5145lv"',
    )

    # Поля для трассировки TODO возможно будут обязательные с ключ актор
    agrType: str | None = Field(default=None)
    traceId: str | None = Field(
        description="Skvoznoi Id для трассировки/Идентификатор всей цепочки вызовов",
        default=None,
    )
    spanId: str | None = Field(
        description="Id для отслеживания цепочки действий внутри сервиса / "
        "Идентификатор отдельной операции внутри цепочки вызовов",
        default=None,
    )
    parentSpanId: str | None = Field(default=None)

    # Возможно, они формируются на стороне агента
    tslgClientVersion: str = Field(
        ...,
        description="Версия клиентского компонента TSLG",
    )  # "Версия клиентского компонента TSLG текущей клиентской части " "библиотеки - 5.6.0")

    namespace: str = Field(default=..., description="Namespace")
    # "имя namespace стенд/контур->код РИС=синоним кода ИС->суффикс, "

    timestamp: float | None = Field(default=None, alias="timestamp")

    mdc: dict[str, str] | None = Field(description="Служебная информация о хосте и процессе", default=None)
