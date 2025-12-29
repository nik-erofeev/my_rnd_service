import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rnd_connectors.tslg.client import KafkaProducerClient


class TslgKafkaHandler(logging.Handler):
    """Logging handler для отправки TSLG-форматированных логов в Kafka."""

    def __init__(
        self,
        producer_client: "KafkaProducerClient",
        level: int = logging.NOTSET,
    ) -> None:
        super().__init__(level)
        self.producer_client = producer_client

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_string = self.format(record)
            self.producer_client.send(log_string)
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        """Flush всех pending сообщений."""
        try:
            self.producer_client.flush()
        except Exception as e:
            print(f"Kafka Handler flush failed: {e}", flush=True)
