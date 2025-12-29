import logging
import sys
from typing import Any

from app.core.config import EnvConfig
from app.core.logger.filters import (
    MessageHeadersFilter,
    MessageKeyFilter,
    RequestIdFilter,
    StagesFilter,
)
from app.core.logger.formatter import ColoredFormatter, create_formatter

# 
from app.core.exceptions import BusinessException
from app.core.logger.formatter import TslgFormatter
from app.core.logger.handlers.fluent import FluentHandler
from app.core.logger.handlers.tslg_kafka import TslgKafkaHandler
from app.core.logger.handlers.tslg_socket import TslgSocketHandler

from rnd_connectors.fluent.client import FluentdClient
from rnd_connectors.fluent.protocols import FluentdConfigProtocol
from rnd_connectors.fluent.schemas import ErrorType, FluentError
from rnd_connectors.tslg.client import KafkaProducerClient
from rnd_connectors.tslg.protocols import TSLGConfigProtocol
# 

# ============================================================================
# Constants
# ============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - requestId: %(request_id)s - %(message)s"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Сохраняем оригинальную фабрику LogRecord один раз
_OLD_LOG_RECORD_FACTORY = logging.getLogRecordFactory()

# Общие фильтры для всех обработчиков
_COMMON_FILTERS = [
    RequestIdFilter(),
    StagesFilter(),
    MessageHeadersFilter(),
    MessageKeyFilter(),
]


# ============================================================================
# Log Record Factory
# ============================================================================

# 
def _custom_log_record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
    """
    Кастомная фабрика LogRecord.

    Добавляет поле 'errors' (по умолчанию пустой список).
    Если есть exc_info — формирует FluentError и кладёт в errors.
    errorType: 'Business' для BusinessException, иначе 'System'.
    """
    record = _OLD_LOG_RECORD_FACTORY(*args, **kwargs)

    if not hasattr(record, "errors") or record.errors == []:
        errors = _build_errors_from_exception(record)
        record.errors = errors

    return record


def _build_errors_from_exception(record: logging.LogRecord) -> list[FluentError]:
    """Извлекает ошибку из LogRecord и формирует список FluentError."""
    errors = []

    exc_info = record.exc_info
    # Проверяем, что exc_info это кортеж с исключением
    if exc_info is not None and isinstance(exc_info, tuple) and exc_info[1] is not None:
        exc = exc_info[1]
        error_type = ErrorType.BUSINESS if isinstance(exc, BusinessException) else ErrorType.SYSTEM
        errors.append(
            FluentError(
                errorCode=type(exc).__name__,
                errorType=error_type,
                errorString=str(exc),
            ),
        )

    # Если ошибок нет — добавляем дефолтный объект
    if not errors:
        errors.append(FluentError())

    return errors
# 


# ============================================================================
# Formatter Creation
# ============================================================================


def _create_default_formatter() -> logging.Formatter:
    """Создает стандартный Formatter."""
    return logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)


def _create_colored_formatter() -> ColoredFormatter:
    """Создает цветной Formatter."""
    return ColoredFormatter(
        LOG_FORMAT,
        datefmt=DATE_FORMAT,
        use_color=True,
    )


def _select_formatter(env_config: EnvConfig) -> logging.Formatter:
    """Выбирает formatter в зависимости от конфига."""
    if env_config.enable_colored_logs:
        return _create_colored_formatter()
    return _create_default_formatter()


# ============================================================================
# Handler Setup
# ============================================================================


def _setup_handler(
    handler: logging.Handler,
    formatter: logging.Formatter,
    log_level: str,
) -> logging.Handler:
    """Настраивает обработчик: добавляет форматтер, уровень и фильтры."""
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    for filter_obj in _COMMON_FILTERS:
        handler.addFilter(filter_obj)
    return handler


def _get_console_handler(env_config: EnvConfig) -> logging.Handler:
    """Создаёт обработчик для вывода логов в консоль."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = _select_formatter(env_config)
    return _setup_handler(handler=handler, formatter=formatter, log_level=env_config.log_level)


# 
def _get_fluentd_handler(fluent_config: FluentdConfigProtocol) -> logging.Handler:
    """Создаёт обработчик для отправки логов в Fluentd."""
    fluentd_client = FluentdClient(fluent_config)
    handler = FluentHandler(fluent_client=fluentd_client, fluent_config=fluent_config)
    formatter = _create_default_formatter()
    return _setup_handler(handler=handler, formatter=formatter, log_level=fluent_config.log_level)


def _get_tslg_tcp_handler(tslg_config: TSLGConfigProtocol) -> logging.Handler:
    """Создает обработчик для отправки логов в TSLG через TCP."""
    handler = TslgSocketHandler(config=tslg_config)
    formatter = _create_default_formatter()
    return _setup_handler(handler=handler, formatter=formatter, log_level=tslg_config.log_level)


def _get_tslg_kafka_handler(tslg_config: TSLGConfigProtocol) -> logging.Handler:
    """Создает обработчик для отправки логов в TSLG через Kafka."""
    producer_client = KafkaProducerClient(config=tslg_config)
    handler = TslgKafkaHandler(producer_client=producer_client)
    formatter = TslgFormatter(config=tslg_config, is_fluentbit=False)
    return _setup_handler(handler=handler, formatter=formatter, log_level=tslg_config.log_level)
# 


# ============================================================================
# Handler Collection
# ============================================================================


def _collect_handlers(env_config: EnvConfig) -> list[logging.Handler]:
    """Собирает список обработчиков на основе конфигов."""
    handlers = [_get_console_handler(env_config)]

    # 
    if env_config.fluent.external_efk_enabled or env_config.fluent.external_db_enabled:
        handlers.append(_get_fluentd_handler(env_config.fluent))

    if env_config.tslg.tcp_enabled:
        try:
            handlers.append(_get_tslg_tcp_handler(env_config.tslg))
        except Exception as e:
            print(f"Failed to init TSLG TCP handler: {e}", file=sys.stderr)

    if env_config.tslg.kafka_enabled:
        try:
            handlers.append(_get_tslg_kafka_handler(env_config.tslg))
        except Exception as e:
            print(f"Failed to init TSLG Kafka handler: {e}", file=sys.stderr)
    # 

    return handlers


# ============================================================================
# Public
# ============================================================================


def setup_logger(env_config: EnvConfig) -> None:
    """
    Настраивает логгер с поддержкой нескольких обработчиков.

    Args:
        env_config: Конфигурация окружения.
    """
    handlers = _collect_handlers(env_config)

    logging.basicConfig(
        handlers=handlers,
        level=env_config.log_level,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # 
    logging.setLogRecordFactory(_custom_log_record_factory)
    logging.raiseExceptions = env_config.fluent.raise_exceptions
    # 


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Получить логгер с указанным именем.

    Args:
        name: Имя логгера. Если None, возвращается корневой логгер.

    Returns:
        Настроенный логгер.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

