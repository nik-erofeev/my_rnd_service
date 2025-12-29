import socket

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from app.core.config import CONFIG
from app.core.logger import get_logger

logger = get_logger(__name__)


class PrometheusService:
    """Сервис для управления метриками Prometheus.

    Реализует все обязательные метрики согласно документации мониторинга.
    """

    def __init__(self) -> None:
        """Инициализация сервиса метрик."""
        self.registry = CollectorRegistry()
        self._setup_metrics()

        # Базовые метки для всех метрик
        self.base_labels = {
            "app_name": CONFIG.prometheus.app_name,
            "project_code": CONFIG.prometheus.project_code,
            "ris_code": CONFIG.prometheus.ris_code,
            "kubernetes_namespace": CONFIG.prometheus.kubernetes_namespace,
            "stateless_replica": socket.gethostname(),
            "tsam_cluster": CONFIG.prometheus.tsam_cluster,
            "tsam_federation_type": CONFIG.prometheus.tsam_federation_type,
        }

        logger.info(f"Prometheus service initialized with base labels: {self.base_labels}")

    def _setup_metrics(self) -> None:
        """Настройка всех метрик согласно документации."""
        # Received messages metrics
        self.received_messages_total = Counter(
            "received_messages_total",
            "The metric is incremented each time the application receives a message",
            labelnames=[
                "app_name",
                "broker",
                "handler",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.received_messages_size_bytes = Histogram(
            "received_messages_size_bytes",
            "The metric is filled with the sizes of received messages",
            labelnames=[
                "app_name",
                "broker",
                "handler",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.received_messages_in_process = Gauge(
            "received_messages_in_process",
            "The metric tracks messages currently being processed",
            labelnames=[
                "app_name",
                "broker",
                "handler",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.received_processed_messages_total = Counter(
            "received_processed_messages_total",
            "The metric counts processed messages by status",
            labelnames=[
                "app_name",
                "broker",
                "handler",
                "status",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.received_processed_messages_duration_seconds = Histogram(
            "received_processed_messages_duration_seconds",
            "The metric is filled with the message processing time",
            labelnames=[
                "app_name",
                "broker",
                "handler",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.received_processed_messages_exceptions_total = Counter(
            "received_processed_messages_exceptions_total",
            "The metric is incremented if any exception occurred while processing a message",
            labelnames=[
                "app_name",
                "broker",
                "handler",
                "exception_type",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        # Published messages metrics
        self.published_messages_total = Counter(
            "published_messages_total",
            "The metric is incremented when messages are sent, regardless of success",
            labelnames=[
                "app_name",
                "broker",
                "destination",
                "status",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.published_messages_duration_seconds = Histogram(
            "published_messages_duration_seconds",
            "The metric is filled with the time the message was sent",
            labelnames=[
                "app_name",
                "broker",
                "destination",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

        self.published_messages_exceptions_total = Counter(
            "published_messages_exceptions_total",
            "The metric increases if any exception occurred while sending a message",
            labelnames=[
                "app_name",
                "broker",
                "destination",
                "exception_type",
                "project_code",
                "ris_code",
                "kubernetes_namespace",
                "stateless_replica",
                "tsam_cluster",
                "tsam_federation_type",
            ],
            registry=self.registry,
        )

    def increment_received_messages(self, handler: str, broker: str = "kafka") -> None:
        """Увеличить счетчик полученных сообщений."""
        labels = {**self.base_labels, "broker": broker, "handler": handler}
        self.received_messages_total.labels(**labels).inc()

    def record_message_size(self, size: int, handler: str, broker: str = "kafka") -> None:
        """Записать размер полученного сообщения."""
        labels = {**self.base_labels, "broker": broker, "handler": handler}
        self.received_messages_size_bytes.labels(**labels).observe(size)

    def increment_messages_in_process(self, handler: str, broker: str = "kafka") -> None:
        """Увеличить счетчик сообщений в процессе обработки."""
        labels = {**self.base_labels, "broker": broker, "handler": handler}
        self.received_messages_in_process.labels(**labels).inc()

    def decrement_messages_in_process(self, handler: str, broker: str = "kafka") -> None:
        """Уменьшить счетчик сообщений в процессе обработки."""
        labels = {**self.base_labels, "broker": broker, "handler": handler}
        self.received_messages_in_process.labels(**labels).dec()

    def increment_processed_messages(self, handler: str, status: str, broker: str = "kafka") -> None:
        """Увеличить счетчик обработанных сообщений."""
        labels = {**self.base_labels, "broker": broker, "handler": handler, "status": status}
        self.received_processed_messages_total.labels(**labels).inc()

    def record_processing_duration(self, duration: float, handler: str, broker: str = "kafka") -> None:
        """Записать время обработки сообщения."""
        labels = {**self.base_labels, "broker": broker, "handler": handler}
        self.received_processed_messages_duration_seconds.labels(**labels).observe(duration)

    def increment_processing_exceptions(self, handler: str, exception_type: str, broker: str = "kafka") -> None:
        """Увеличить счетчик исключений при обработке."""
        labels = {
            **self.base_labels,
            "broker": broker,
            "handler": handler,
            "exception_type": exception_type,
        }
        self.received_processed_messages_exceptions_total.labels(**labels).inc()

    def increment_published_messages(self, destination: str, status: str, broker: str = "kafka") -> None:
        """Увеличить счетчик опубликованных сообщений."""
        labels = {
            **self.base_labels,
            "broker": broker,
            "destination": destination,
            "status": status,
        }
        self.published_messages_total.labels(**labels).inc()

    def record_publish_duration(self, duration: float, destination: str, broker: str = "kafka") -> None:
        """Записать время публикации сообщения."""
        labels = {**self.base_labels, "broker": broker, "destination": destination}
        self.published_messages_duration_seconds.labels(**labels).observe(duration)

    def increment_publish_exceptions(self, destination: str, exception_type: str, broker: str = "kafka") -> None:
        """Увеличить счетчик исключений при публикации."""
        labels = {
            **self.base_labels,
            "broker": broker,
            "destination": destination,
            "exception_type": exception_type,
        }
        self.published_messages_exceptions_total.labels(**labels).inc()

    def generate_metrics(self) -> bytes:
        """Сгенерировать метрики в формате Prometheus."""
        return generate_latest(self.registry)


# Глобальный экземпляр сервиса метрик
prometheus_service = PrometheusService()
