from typing import Protocol


class TSLGConfigProtocol(Protocol):
    # Включение/выключение TSLG логирования
    tcp_enabled: bool
    kafka_enabled: bool
    log_level: str

    # Параметры подключения к TSLG Agent
    host: str
    port: int

    app_name: str  # "python_online_rag_3287_shturman_1"
    app_type: str  # "Тип приложения (PYTHON/JAVA/NODEJS/GO)"
    project_code: str  # "TSLG"
    ris_code: str  # "1655_21"

    client_version: str  # "5.6.0"

    namespace: str  # "namespace"
    env_type: str | int  # Тип окружения K8S | VM | FAAS ...

    # Дополнительные параметры
    aggregation_type: str  # тип агрегации (TRACING/OPENSHIFT_EVENT/...)

    # Параметры подключения к Kafka
    kafka_topic: str
    kafka_bootstrap_servers: str
    kafka_cafile: str
    kafka_certfile: str
    kafka_keyfile: str
    kafka_password: str
