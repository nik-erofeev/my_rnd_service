import logging
import sys
from typing import ClassVar, Literal

from colorama import Fore, Style

# 
import socket
import uuid
from datetime import datetime, timezone
from time import time
from typing import Any

from app.core.exceptions import BusinessException
from rnd_connectors.fluent.schemas import ErrorType, FluentError
from rnd_connectors.tslg.protocols import TSLGConfigProtocol
from rnd_connectors.tslg.schemas import TSLGMsgSchemas
from app.core.logger.utils import is_valid_uuid
# 


# Формат логирования
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - requestId: %(request_id)s - %(message)s"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class ColoredFormatter(logging.Formatter):
    """Форматтер для цветного вывода в консоль."""

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_color: bool = True,
    ) -> None:
        super().__init__(fmt, datefmt, style)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color and record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            # Только levelname цветной
            record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


def create_formatter() -> logging.Formatter:
    """Создает Formatter с общим форматом логов."""
    return logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)


# 
class TslgFormatter(logging.Formatter):
    """Форматтер для преобразования LogRecord в JSON‑строку для TSLG Agent."""

    def __init__(self, config: TSLGConfigProtocol, is_fluentbit: bool) -> None:
        super().__init__()
        self.tslg_config = config
        self._host = socket.gethostname()
        try:
            self._pod_ip = socket.gethostbyname(self._host)
        except Exception:
            self._pod_ip = "127.0.0.1"

        self.is_fluentbit = is_fluentbit

    def format(self, record: logging.LogRecord) -> str:
        """Форматирование LogRecord в JSON строку для TSLG."""
        tslg_dict = self._build_base_dict(record)
        self._add_mdc_if_needed(record=record, tslg_dict=tslg_dict)
        self._add_stack_trace_if_needed(record=record, tslg_dict=tslg_dict)
        self._add_tracing_if_needed(record=record, tslg_dict=tslg_dict)
        self._add_optional_fields(tslg_dict=tslg_dict)

        return TSLGMsgSchemas(**tslg_dict).model_dump_json(by_alias=True)

    def _build_base_dict(self, record: logging.LogRecord) -> dict[str, Any]:
        """Строит базовый словарь параметров логирования."""
        time_create_log = self._format_timestamp(record.created)
        event_id = self._get_event_id(record)

        return {
            "appName": self.tslg_config.app_name,
            "appType": self.tslg_config.app_type,
            "envType": self.tslg_config.env_type,
            "risCode": self.tslg_config.ris_code,
            "projectCode": self.tslg_config.project_code,
            "level": logging.getLevelName(record.levelno),
            "text": record.getMessage(),
            "callerMethod": f"{record.filename}.{record.funcName}",
            "callerLine": record.lineno,
            "PID": record.process,
            "threadName": record.threadName,
            "eventId": event_id,
            "localTime": time_create_log,
            "podName": self._pod_ip,
            "tec": {"podIp": self._pod_ip},
            "loggerName": record.name,
            "hostName": self._host,
        }

    @staticmethod
    def _format_timestamp(created: float) -> str:
        """Форматирует timestamp в ISO 8601."""
        dt = datetime.fromtimestamp(created, timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    @staticmethod
    def _get_event_id(record: logging.LogRecord) -> str:
        """Получает или генерирует event_id."""
        request_id = getattr(record, "request_id", None)
        # Исправлено: явное приведение к str(request_id) удовлетворяет линтер
        return str(request_id) if is_valid_uuid(request_id) else str(uuid.uuid4())

    @staticmethod
    def _add_mdc_if_needed(record: logging.LogRecord, tslg_dict: dict[str, Any]) -> None:
        """Добавляет MDC если есть request_id."""
        request_id = getattr(record, "request_id", None)
        if request_id is not None and request_id != "-":
            tslg_dict["mdc"] = {"request_id": request_id}

    def _add_stack_trace_if_needed(self, record: logging.LogRecord, tslg_dict: dict[str, Any]) -> None:
        """Добавляет stack trace если есть исключение."""
        if record.exc_info:
            exc_info = record.exc_info if isinstance(record.exc_info, tuple) else sys.exc_info()
            if exc_info and exc_info != (None, None, None):
                tslg_dict["stack"] = self.formatException(exc_info)
        elif record.stack_info:
            tslg_dict["stack"] = self.formatStack(record.stack_info)

    def _add_tracing_if_needed(self, record: logging.LogRecord, tslg_dict: dict[str, Any]) -> None:
        """Добавляет данные трассировки если включена."""
        if self.tslg_config.aggregation_type == "TRACING":
            tslg_dict["agrType"] = self.tslg_config.aggregation_type
            tslg_dict["traceId"] = self._extract_uuid(record=record, attr_name="trace_id")
            tslg_dict["spanId"] = self._extract_uuid(record=record, attr_name="span_id")

    @staticmethod
    def _extract_uuid(record: logging.LogRecord, attr_name: str) -> str | None:
        """Извлекает и конвертирует UUID из атрибута record."""
        value = getattr(record, attr_name, None)
        return uuid.UUID(value).hex if is_valid_uuid(value) else None

    def _add_optional_fields(self, tslg_dict: dict[str, Any]) -> None:
        """Добавляет опциональные поля."""
        if not self.is_fluentbit:
            tslg_dict["tslgClientVersion"] = self.tslg_config.client_version

        tslg_dict["timestamp"] = time()  # type: ignore
        tslg_dict["namespace"] = self.tslg_config.namespace
# 
