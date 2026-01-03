from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# Базовый класс конфига
class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        env_nested_delimiter="__",
    )


class ProjectConfig(Config):
    name: str
    version: str
    description: str

    model_config = SettingsConfigDict(env_prefix="PROJECT__")


class PrometheusConfig(Config):
    enabled: bool
    app_name: str
    project_code: str
    ris_code: str
    kubernetes_namespace: str
    tsam_cluster: str
    tsam_federation_type: str

    model_config = SettingsConfigDict(env_prefix="PROMETHEUS__")


class APIConfig(Config):
    host: str
    port: int
    debug: bool
    project_name: str  # = "Example API"
    description: str  # = "Example API description 🚀"
    version: str  # = "1.0.0"
    v1: str = "/v1"
    openapi_url: str  # = "/api/v1/openapi.json"
    echo: bool = False
    topik: str = "example-send-topic"
    cors_origin_regex: str = r"(http://|https://)?(.*\.)?(qa|stage|localhost|0.0.0.0)" r"(\.ru)?(:\d+)?$"

    model_config = SettingsConfigDict(env_prefix="API__")


class ReadKafkaConfig(Config):
    bootstrap_servers: list[str]
    topic_in: str
    group_id: str
    max_workers: int

    use_ssl: bool = False
    ssl_check_hostname: bool = False

    # Параметры поллинга (как в примере)
    auto_offset_reset: str = "earliest"
    max_poll_interval_ms: int = 300000
    max_poll_records: int = 500

    model_config = SettingsConfigDict(env_prefix="READ_KAFKA__")


class WriteKafkaConfig(Config):
    bootstrap_servers: list[str]
    topic_out: str

    model_config = SettingsConfigDict(env_prefix="WRITE_KAFKA__")


class SSLKafkaConfig(Config):
    cafile: str
    certfile: str
    keyfile: str
    password: str

    additional_broker_config: dict = {}  # type: ignore

    model_config = SettingsConfigDict(env_prefix="SSL_KAFKA__")


class FluentConfig(Config):
    log_all: bool
    external_efk_enabled: bool
    external_db_enabled: bool
    app_name: str
    namespace: str
    log_level: str
    workers: int
    url: str
    verify: bool = False
    cert_path: str | None = None
    index_prefix: str
    source_type: str
    environment: str
    timeout: float
    raise_exceptions: bool

    model_config = SettingsConfigDict(
        env_prefix="FLUENT__",
    )

    @property
    def index_name(self) -> str:
        return f"{self.index_prefix}__{self.app_name}"


class TSLGConfig(Config):
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

    model_config = SettingsConfigDict(env_prefix="TSLG__")



class SmithLangChainConfig(Config):
    tracing_v2: bool #= False
    api_key: str | None = None
    project: str #= "default"
    endpoint: str #= "https://api.smith.langchain.com"

    model_config = SettingsConfigDict(env_prefix="SMITH__")


class EnvConfig(Config):
    project: ProjectConfig = ProjectConfig()  # type: ignore[call-arg]
    prometheus: PrometheusConfig = PrometheusConfig()  # type: ignore[call-arg]
    api: APIConfig = APIConfig()  # type: ignore[call-arg]
    read_kafka: ReadKafkaConfig = ReadKafkaConfig()  # type: ignore[call-arg]
    write_kafka: WriteKafkaConfig = WriteKafkaConfig()  # type: ignore[call-arg]
    ssl_kafka: SSLKafkaConfig = SSLKafkaConfig()  # type: ignore[call-arg]
    fluent: FluentConfig = FluentConfig()  # type: ignore[call-arg]
    tslg: TSLGConfig = TSLGConfig()  # type: ignore[call-arg]
    smith: SmithLangChainConfig = SmithLangChainConfig()  # type: ignore[call-arg]
    log_level: str = "INFO"
    enable_colored_logs: bool = True  # Added here



CONFIG = EnvConfig()

# # Export LangChain settings to environment variables for the SDK
if CONFIG.smith.api_key:
    import os
    # нужны конкретно эти переменные, иначе не дойдет
    os.environ["LANGCHAIN_TRACING_V2"] = str(CONFIG.smith.tracing_v2).lower()
    os.environ["LANGCHAIN_API_KEY"] = CONFIG.smith.api_key
    os.environ["LANGCHAIN_PROJECT"] = CONFIG.smith.project
    os.environ["LANGCHAIN_ENDPOINT"] = CONFIG.smith.endpoint
