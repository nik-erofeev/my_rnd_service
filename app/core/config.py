from dotenv import find_dotenv
from pydantic import Field
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
    # https://smith.langchain.com/settings
    tracing_v2: bool = Field(default=True, alias="LANGCHAIN_TRACING_V2")
    api_key: str = Field(..., alias="LANGCHAIN_API_KEY")
    project: str = Field(..., alias="LANGCHAIN_PROJECT")
    endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGCHAIN_ENDPOINT")


class LangfuseConfig(Config):
    secret_key: str = Field(..., alias="LANGFUSE_SECRET_KEY")
    public_key: str = Field(..., alias="LANGFUSE_PUBLIC_KEY")
    base_url: str = Field(..., alias="LANGFUSE_BASE_URL")
    enable: bool = True


# ─────────── RND TOKEN MANAGER ───────────
class RNDTokenManagerConfig(Config):
    login: str
    password: str
    url: str
    verify: bool = False

    model_config = SettingsConfigDict(env_prefix="RND_TOKEN__")


# ─────────── YANDEX / LLM  ───────────
class RNDYandexConfig(Config):
    api_url: str
    folder_id: str
    model: str
    temperature: float
    max_tokens: int
    use_ssl: bool = False
    stream: bool = False
    reasoning_mode: str | None = None

    model_config = SettingsConfigDict(env_prefix="RND_YANDEX__")


# ─────────── TYK / LLM  ───────────
class TYKYandexConfig(Config):
    api_url: str
    folder_id: str
    model: str
    temperature: float
    max_tokens: int
    use_ssl: bool = False

    use_tyk: bool = False

    model_config = SettingsConfigDict(env_prefix="TYK_YANDEX__")


# ─────────── EPA TOKEN ───────────
class EPATokenManagerConfig(Config):
    login: str
    password: str
    url: str
    verify: bool = False

    model_config = SettingsConfigDict(env_prefix="EPA_TOKEN__")


class RagConfig(Config):
    # Параметры MultiQuery Ensemble Retriever
    n: int  # Сколько раз LLM переформулирует запрос
    k: int  # Документов от векторного поиска на каждый переформулированный запрос
    relevance_threshold: float  # = 0.55 # Порог релевантности для векторного поиска
    use_hybrid_search: bool  # = True  # гибридный поиск (True = векторный + BM25)
    bm25_weight: float  # = 0.55  # вес BM25 в гибридном поиске
    use_answer_checker: bool  # = False
    n_best: int  # Количество лучших результатов для реранкера

    model_config = SettingsConfigDict(env_prefix="RAG__")


# ─────────── EMBEDDING ───────────
class EmbeddingConfig(Config):
    model: str
    device: str  # "cuda" | "mps" | "cpu"

    model_config = SettingsConfigDict(env_prefix="EMBEDDING__")


# ─────────── OPENSEARCH ───────────
class OpenSearchConfig(Config):
    url: str
    index_name: str
    login: str
    password: str

    model_config = SettingsConfigDict(env_prefix="OPENSEARCH__")


class EnvConfig(Config):
    # LLM
    tyk_yandex_config: TYKYandexConfig = TYKYandexConfig()  # type: ignore[call-arg]
    epa_token: EPATokenManagerConfig = EPATokenManagerConfig()  # type: ignore[call-arg]
    rnd_yandex_config: RNDYandexConfig = RNDYandexConfig()  # type: ignore[call-arg]
    rnd_token_manager_config: RNDTokenManagerConfig = RNDTokenManagerConfig()  # type: ignore[call-arg]

    embedding: EmbeddingConfig = EmbeddingConfig()  # type: ignore[call-arg]
    rag: RagConfig = RagConfig()  # type: ignore[call-arg]
    open_search: OpenSearchConfig = OpenSearchConfig()  # type: ignore[call-arg]

    project: ProjectConfig = ProjectConfig()  # type: ignore[call-arg]
    prometheus: PrometheusConfig = PrometheusConfig()  # type: ignore[call-arg]
    api: APIConfig = APIConfig()  # type: ignore[call-arg]
    read_kafka: ReadKafkaConfig = ReadKafkaConfig()  # type: ignore[call-arg]
    write_kafka: WriteKafkaConfig = WriteKafkaConfig()  # type: ignore[call-arg]
    ssl_kafka: SSLKafkaConfig = SSLKafkaConfig()  # type: ignore[call-arg]
    fluent: FluentConfig = FluentConfig()  # type: ignore[call-arg]
    tslg: TSLGConfig = TSLGConfig()  # type: ignore[call-arg]
    log_level: str = "INFO"
    enable_colored_logs: bool = True  # Added here

    langfuse: LangfuseConfig = LangfuseConfig()  # type: ignore[call-arg]
    smith: SmithLangChainConfig = SmithLangChainConfig()  # type: ignore[call-arg]


CONFIG = EnvConfig()

# # нужны конкретно эти переменные, иначе не дойдет
# if CONFIG.smith.tracing_v2:  # enable
#     import os
#
#     os.environ["LANGCHAIN_TRACING_V2"] = str(CONFIG.smith.tracing_v2).lower()
#     os.environ["LANGCHAIN_API_KEY"] = CONFIG.smith.api_key
#     os.environ["LANGCHAIN_PROJECT"] = CONFIG.smith.project
#     os.environ["LANGCHAIN_ENDPOINT"] = CONFIG.smith.endpoint

if CONFIG.langfuse.enable:
    import os

    # langfuse
    os.environ["LANGFUSE_SECRET_KEY"] = CONFIG.langfuse.secret_key
    os.environ["LANGFUSE_PUBLIC_KEY"] = CONFIG.langfuse.public_key
    os.environ["LANGFUSE_BASE_URL"] = CONFIG.langfuse.base_url
