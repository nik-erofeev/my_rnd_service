import sys
import time
from collections.abc import Awaitable, Callable
from types import FrameType
from typing import TYPE_CHECKING, Any

from faststream import BaseMiddleware, PublishCommand, StreamMessage

if TYPE_CHECKING:
    from faststream._internal.context.repository import ContextRepo

from app.core.config import CONFIG
from app.core.logger import get_logger
from app.services.prometheus_service import prometheus_service

logger = get_logger(__name__)


class PrometheusMiddleware(BaseMiddleware):  # type: ignore[misc]
    """Мидлваре для сбора метрик Prometheus."""

    def __init__(self, msg: Any, *, context: "ContextRepo") -> None:
        """Инициализация мидлваре."""
        super().__init__(msg, context=context)
        self._processing_start_time: float | None = None

        if not CONFIG.prometheus.enabled:
            logger.info("Мидлваре Prometheus отключено в конфигурации")
            return

        logger.info("Мидлваре Prometheus инициализировано")

    async def on_receive(self) -> Any:
        if not CONFIG.prometheus.enabled:
            return await super().on_receive()

        handler_name = self._get_handler_name()
        prometheus_service.increment_received_messages(handler=handler_name)

        message_size = self._get_message_size()
        if message_size > 0:
            prometheus_service.record_message_size(size=message_size, handler=handler_name)

        logger.info(f"Получено сообщение - обработчик={handler_name}, размер={message_size} байт")
        return await super().on_receive()

    async def consume_scope(
        self,
        call_next: Callable[[StreamMessage[Any]], Awaitable[Any]],
        msg: StreamMessage[Any],
    ) -> Any:
        if not CONFIG.prometheus.enabled:
            return await call_next(msg)

        handler_name = self._get_handler_name()
        prometheus_service.increment_messages_in_process(handler=handler_name)
        self._processing_start_time = time.time()

        try:
            result = await call_next(msg)
            prometheus_service.increment_processed_messages(handler=handler_name, status="success")
            logger.info(f"Сообщение успешно обработано - обработчик={handler_name}")
            return result

        except Exception as e:
            exception_type = type(e).__name__
            prometheus_service.increment_processed_messages(handler=handler_name, status="error")
            prometheus_service.increment_processing_exceptions(handler=handler_name, exception_type=exception_type)
            logger.info(f"Ошибка при обработке сообщения - обработчик={handler_name}, исключение={exception_type}")
            raise

        finally:
            prometheus_service.decrement_messages_in_process(handler=handler_name)
            if self._processing_start_time is not None:
                duration = time.time() - self._processing_start_time
                prometheus_service.record_processing_duration(duration=duration, handler=handler_name)
                logger.info(f"Длительность обработки сообщения - обработчик={handler_name}, время={duration:.3f}с")

    async def publish_scope(
        self,
        call_next: Callable[[PublishCommand], Awaitable[Any]],
        cmd: PublishCommand,
    ) -> Any:
        if not CONFIG.prometheus.enabled:
            return await call_next(cmd)

        destination = self._get_destination(cmd)
        publish_start_time = time.time()

        try:
            result = await call_next(cmd)
            prometheus_service.increment_published_messages(destination=destination, status="success")
            logger.info(f"Сообщение успешно опубликовано - направление={destination}")
            return result

        except Exception as e:
            exception_type = type(e).__name__
            prometheus_service.increment_published_messages(destination=destination, status="error")
            prometheus_service.increment_publish_exceptions(destination=destination, exception_type=exception_type)
            logger.info(f"Ошибка при публикации сообщения - направление={destination}, исключение={exception_type}")
            raise

        finally:
            duration = time.time() - publish_start_time
            prometheus_service.record_publish_duration(duration=duration, destination=destination)
            logger.info(f"Длительность публикации сообщения - направление={destination}, время={duration:.3f}с")

    def _get_handler_name(self) -> str:
        """Получить имя обработчика из контекста."""
        try:
            # Пытаемся получить handler из контекста
            if hasattr(self.context, "get_local"):
                handler_info = self.context.get_local("handler", None)
                if handler_info and hasattr(handler_info, "__name__"):
                    logger.info(f"Определен обработчик из контекста: {handler_info.__name__}")
                    return str(handler_info.__name__)

            # Альтернативный способ через стек вызовов
            frame: FrameType | None = sys._getframe(1)
            while frame is not None:
                if "handler" in frame.f_code.co_name or "process" in frame.f_code.co_name:
                    logger.info(f"Определен обработчик через стек вызовов: {frame.f_code.co_name}")
                    return frame.f_code.co_name
                frame = frame.f_back  # mypy: frame теперь может быть None, тип правильный

        except Exception as e:
            logger.info(f"Не удалось определить имя обработчика: {e}")

        return "unknown_handler"

    def _calculate_size(self, obj: Any) -> int:
        if obj is None:
            return 0
        if isinstance(obj, (bytes, bytearray)):
            return len(obj)
        if isinstance(obj, str):
            return len(obj.encode("utf-8"))
        for attr in ("body", "value", "data"):
            if hasattr(obj, attr):
                return self._calculate_size(getattr(obj, attr))
        if hasattr(obj, "__len__"):
            return len(str(obj).encode("utf-8"))
        return 0

    @staticmethod
    def _get_destination(cmd: PublishCommand) -> str:
        for attr in ("topic", "queue", "channel", "subject", "destination", "routing_key"):
            if hasattr(cmd, attr):
                return str(getattr(cmd, attr))
        return CONFIG.write_kafka.topic_out

    def _get_message_size(self) -> int:
        """Получить размер сообщения в байтах."""
        try:
            if self.msg is not None:
                # Попытка определить тело сообщения из известных атрибутов
                for attr in ("body", "value", "data"):
                    if hasattr(self.msg, attr):
                        return self._calculate_size(getattr(self.msg, attr))
                # Если нет специальных атрибутов, берём сам объект
                return self._calculate_size(self.msg)
        except Exception as e:
            logger.info(f"Не удалось определить размер сообщения: {e}")
        return 0
