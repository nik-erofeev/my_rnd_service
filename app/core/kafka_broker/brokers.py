from faststream.kafka import KafkaBroker
from faststream.kafka.prometheus import KafkaPrometheusMiddleware

from app.core.config import CONFIG
from app.core.kafka_broker.middlewares import (
    AutoPublishMiddleware,
    PrometheusMiddleware,
    RequestContextMiddleware,
    exc_middleware,
)
from app.core.kafka_broker.utils.ssl_config import ssl_and_update_broker_kwargs
from app.core.logger import get_logger
from app.services.prometheus_service import prometheus_service

logger = get_logger(__name__)

# Общий реестр метрик для /metrics
registry = prometheus_service.registry
kafka_prometheus_middleware = KafkaPrometheusMiddleware(registry=registry)


broker = KafkaBroker(
    CONFIG.read_kafka.bootstrap_servers,
    logger=logger,
    middlewares=[
        # 1.  # кастомный middleware
        PrometheusMiddleware,
        # 2. # KafkaPrometheusMiddleware для готового дашборда # опционально
        kafka_prometheus_middleware,
        # 3. RequestContext (headers, key, validation)
        RequestContextMiddleware,
        # 4. AutoPublish (публикация результата)
        AutoPublishMiddleware,
        # 5. Global Error Handler
        exc_middleware,
    ],
    **ssl_and_update_broker_kwargs(),
)
