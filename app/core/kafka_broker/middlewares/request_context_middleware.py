from collections.abc import Awaitable, Callable
from typing import Any

from faststream import BaseMiddleware, PublishCommand, StreamMessage
from pydantic import ValidationError

from app.core.kafka_broker.utils.header_validation import HeadersValidator
from app.core.logger import get_logger
from app.core.logger.context_storage import message_headers, message_key, request_id, stages_context
from rnd_connectors.fluent.schemas import StagesKafkaMessages

logger = get_logger(__name__)


class RequestContextMiddleware(BaseMiddleware):
    """
    Мидлвар для инициализации контекста (request-scoped) из сообщения Kafka.

    Назначение:
    - Извлекает и сохраняет headers и key из Kafka-сообщения в contextvars
    - Инициализирует request_id
    - Инициализирует stages (этапы обработки)
    - ВАЛИДАЦИЯ заголовков (наличие обязательных полей)

    Порядок выполнения: Первым (или одним из первых) в цепочке.
    """

    async def consume_scope(
        self,
        call_next: Callable[[StreamMessage[Any]], Awaitable[Any]],
        msg: StreamMessage[Any],
    ) -> Any:
        self.msg = msg
        # 1. Извлекаем и сохраняем headers (request_id и пр.)
        await self._process_headers()

        # 2. Извлекаем и сохраняем key
        await self._process_message_key()

        # 3. Проверка на пустое тело (как в vtb_3287)
        if not msg.body:
            logger.warning("RequestContextMiddleware: Пустое body")
            raise ValueError("Пустое body")

        return await super().consume_scope(call_next, msg)

    async def _process_headers(self) -> None:
        """Извлекает заголовки из сообщения, ВАЛИДИРУЕТ их и пишет в contextvars."""
        if not self.msg:
            return
        try:
            headers_src = self.msg.headers  # type: ignore[attr-defined]
        except AttributeError as err:
            logger.error("RequestContextMiddleware: headers отсутствуют у сообщения")
            # Валидация заголовков требует их наличия
            raise ValidationError("Headers are missing", HeadersValidator) from err

        if not headers_src:
            logger.warning("RequestContextMiddleware: headers пустые")
            raise ValidationError("Headers are empty", HeadersValidator) from None

        headers_dict: dict[str, str] = {}
        # FastStream headers могут быть dict или list of tuples
        if isinstance(headers_src, dict):
            headers_dict = headers_src
        else:
            for item in headers_src:  # type: ignore[union-attr]
                parsed = self._parse_header_item(item)
                if parsed is None:
                    continue
                k, v = parsed
                headers_dict[k] = v

        # ВАЛИДАЦИЯ ЗАГОЛОВКОВ
        # Используем strict=False (проверяем только наличие полей), т.к. строгая валидация типов Pydantic может быть избыточна здесь,  # noqa: E501
        # но если пользователь хочет строгости - можно strict=True.
        # В vtb_3287 decoder использует Pydantic validation.
        validated = HeadersValidator.validate_headers(headers_dict, strict=True)

        if validated is None:
            # validate_headers возвращает None при ошибке и логирует её.
            # Нам нужно выбросить исключение, чтобы error_handler его поймал.
            missing = HeadersValidator.get_missing_fields(headers_dict)
            raise ValueError(f"Invalid headers. Missing: {missing}")

        # Если успешно - используем (возможно очищенные) заголовки
        final_headers = validated

        logger.debug(f"RequestContextMiddleware: распознано заголовков: {len(final_headers)}")
        message_headers.set(final_headers)

        # messageId vs requestId: теперь используем только requestId
        requests_id_val = final_headers.get("requestId")
        if requests_id_val is not None:
            # Устанавливаем request_id для логгера и трассировки
            request_id.set(str(requests_id_val))
            # Инициализируем контейнер стадий обработки
            stages_context.set(StagesKafkaMessages())

    @staticmethod
    def _parse_header_item(item: Any) -> tuple[str, str] | None:
        """Безопасно парсит заголовок (key, value) в пару строк."""
        # 1) Проверка структуры данных

        EXPECTED_PARTS = 2
        if not isinstance(item, (tuple, list)) or len(item) != EXPECTED_PARTS:
            return None

        k, v = item

        # 2) Проверяем и преобразуем ключ
        if not isinstance(k, (str, bytes, int, float)):
            return None
        try:
            key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
        except Exception:
            logger.error("RequestContextMiddleware: не удалось декодировать ключ заголовка")
            return None

        # 3) Проверяем и преобразуем значение
        if v is None:
            return None
        try:
            if isinstance(v, bytes):
                val = v.decode("utf-8")
            else:
                val = str(v)
        except Exception:
            logger.error("RequestContextMiddleware: не удалось декодировать значение заголовка")
            return None

        return key, val

    async def _process_message_key(self) -> None:
        """Извлекает ключ Kafka-сообщения и сохраняет его в contextvars (без исключений)."""
        if not self.msg:
            return
        key = self._extract_message_key()
        # Сохраняем даже None — дальше по цепочке это учитывается
        message_key.set(key)

    def _extract_message_key(self) -> bytes | None:
        """Безопасно извлекает ключ Kafka (сначала проверяем msg.key, потом msg.raw_message.key)."""
        if not self.msg:
            return None

        # Сначала пробуем напрямую через msg.key (как в FastStream)
        try:
            key = self.msg.key  # type: ignore[attr-defined]
            if key is not None:
                return key
        except AttributeError:
            pass

        # Если нет напрямую, пробуем через raw_message.key
        try:
            raw = self.msg.raw_message  # type: ignore[attr-defined]
            if raw is not None:
                key = raw.key  # type: ignore[attr-defined]
                if key is not None:
                    return key
        except (AttributeError, TypeError):
            pass

        return None

    async def publish_scope(
        self,
        call_next: Callable[[PublishCommand], Awaitable[Any]],
        cmd: PublishCommand,
    ) -> Any:
        return await super().publish_scope(call_next, cmd)
