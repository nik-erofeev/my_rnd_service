# my_rnd_service/app/core/logger/handlers/fluent.py
import atexit
import logging
import socket
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from urllib3.exceptions import InsecureRequestWarning

from app.core.config import CONFIG
from rnd_connectors.fluent.client import FluentdClient
from rnd_connectors.fluent.protocols import FluentdConfigProtocol
from rnd_connectors.fluent.schemas import FluentDBLog, FluentELKLog, FluentEvent, FluentExt, FluentMessage

executor = ThreadPoolExecutor(max_workers=CONFIG.fluent.workers)
atexit.register(executor.shutdown, wait=True)  # чтобы последние логи дошли

warnings.filterwarnings("ignore", category=InsecureRequestWarning, module="urllib3")


class FluentHandler(logging.Handler):
    """Обработчик логирования для отправки логов в Fluentd."""

    def __init__(
        self,
        fluent_client: FluentdClient,
        fluent_config: FluentdConfigProtocol,
        level: int = logging.NOTSET,
    ) -> None:
        super().__init__(level)
        self.fluent_client = fluent_client
        self.fluent_config = fluent_config
        self.node = socket.gethostname()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Overwrite method to push logs to fluentd.
        :param record: LogRecord
        """
        if self.fluent_config.log_all:
            record.action = self.fluent_config.app_name
        if not hasattr(record, "action"):
            return

        action = record.action
        errors = record.errors if hasattr(record, "errors") else []
        stages = getattr(record, "stages", None)  # Добавляем stages из record, если есть

        created_dt = datetime.fromtimestamp(record.created, tz=UTC)
        # created_dt = datetime.fromtimestamp(timestamp=record.created, tz=timezone.utc)

        # EFK
        time = int(created_dt.timestamp())
        timestamp = created_dt.isoformat(sep="T", timespec="milliseconds")

        # DB
        event_date = created_dt.isoformat()

        if self.fluent_config.external_efk_enabled:
            msg_efk = FluentELKLog(
                index=self.fluent_config.index_name,
                sourceType=self.fluent_config.source_type,
                # time=int(datetime.timestamp(time_now)),  # не правильно
                # timestamp=time_now.isoformat(sep="T", timespec="milliseconds"),  # не правильно
                time=time,
                timestamp=timestamp,
                rqId=record.request_id,  # type: ignore
                event=FluentEvent(
                    severity=str(logging.getLevelName(record.levelno)),
                    message=FluentMessage(
                        action=action,
                        message=record.getMessage(),
                        environment=self.fluent_config.environment,
                        node=self.node,
                        errors=errors,
                        ext=FluentExt(
                            serviceName=self.fluent_config.app_name,
                            openshiftName=self.fluent_config.namespace,
                            stages=stages,  # Прокидываем stages в ext
                        ),
                    ),
                ),
            )

            executor.submit(self.fluent_client.send_to_efk, msg_efk)

        if self.fluent_config.external_db_enabled:
            msg_db = FluentDBLog(
                source_name=self.fluent_config.index_name,
                request_id=record.request_id,  # type: ignore
                log_level=str(logging.getLevelName(record.levelno)),
                logger_name=record.name,
                host_name=socket.gethostname(),
                thread_name=record.threadName,
                message=record.getMessage(),
                event_date=event_date,
            )
            executor.submit(self.fluent_client.send_to_db, msg_db)
