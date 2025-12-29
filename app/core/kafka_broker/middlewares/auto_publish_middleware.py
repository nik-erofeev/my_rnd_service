import time
from collections.abc import Awaitable, Callable
from typing import Any

from faststream import BaseMiddleware, PublishCommand, StreamMessage

from app.core.config import CONFIG
from app.core.kafka_broker.schemas import HeadersTopikOut
from app.core.logger import get_logger
from app.core.logger.context_storage import message_headers, message_key, reset_request_context

logger = get_logger(__name__)


class AutoPublishMiddleware(BaseMiddleware):  # type: ignore[misc]
    """
    Автопубликует результат хендлера в выходной топик, если он не None.

    Назначение:
    - Автоматически публикует результат выполнения хендлера в выходной топик (CONFIG.write_kafka.topic_out)
    - Использует key из contextvars (сохранен RequestContextMiddleware)
    - Headers автоматически подставляются
    - Логирует результат публикации (успех/ошибка/пустой результат)
    - Измеряет время обработки сообщения

    Порядок выполнения: После RetryMiddleware, перед exc_middleware.
    Перехватывает результат хендлера и публикует его в Kafka.
    """

    async def consume_scope(
        self,
        call_next: Callable[[StreamMessage[Any]], Awaitable[Any]],
        msg: StreamMessage[Any],
    ) -> Any:
        started_at = time.perf_counter()
        result: Any | None = None
        publish_success = False
        publish_error: Exception | None = None
        processing_error: Exception | None = None

        try:
            result = await call_next(msg)

            if result is not None:
                try:
                    await self._publish_result(result)
                    publish_success = True
                except Exception as e:  # noqa: PERF203
                    publish_error = e
                    logger.error(f"❌ Ошибка публикации результата: {e}", exc_info=True)

            return result
        except Exception as e:  # noqa: PERF203
            processing_error = e
            raise
        finally:
            elapsed = time.perf_counter() - started_at
            r = msg.raw_message
            partition = r.partition
            offset = r.offset

            if processing_error:
                logger.error(
                    f"❌ Ошибка обработки: {processing_error} | topic={CONFIG.write_kafka.topic_out} | partition={partition} | offset={offset} | время:⏱️ {elapsed:.3f}с",  # noqa: E501
                )
            elif result is None:
                logger.info(
                    f"ℹ️ Пустой результат | topic={CONFIG.write_kafka.topic_out} | partition={partition} | offset={offset} | время:⏱️ {elapsed:.3f}с",  # noqa: E501
                )
            elif publish_success:
                logger.info(
                    f"✅ Результат опубликован | topic={CONFIG.write_kafka.topic_out} | partition={partition} | offset={offset} | время:⏱️ {elapsed:.3f}с",  # noqa: E501
                )
            elif publish_error:
                logger.error(
                    f"❌ Ошибка публикации: {publish_error} | topic={CONFIG.write_kafka.topic_out} | partition={partition} | offset={offset} | время:⏱️ {elapsed:.3f}с",  # noqa: E501
                )
            else:
                logger.warning(
                    f"⚠️ Неожиданное состояние AutoPublishMiddleware | topic={CONFIG.write_kafka.topic_out} | partition={partition} | offset={offset} | время:⏱️ {elapsed:.3f}с",  # noqa: E501
                )
            # при успехе сбрасываем, при ошибке сбрасывается в exc
            if not processing_error:
                reset_request_context()

    @staticmethod
    async def _publish_result(result: Any) -> None:
        from app.core.kafka_broker.brokers import broker

        message_data = result.model_dump(exclude_none=True) if hasattr(result, "model_dump") else result

        # меняем хедеры (если меняются)
        current_headers = message_headers.get() or {}
        new_headers = HeadersTopikOut(
            requestId=str(current_headers.get("requestId")),
        ).model_dump(exclude_none=True)

        key = message_key.get()

        logger.info(
            f"📤Отправка сообщения в топик: {CONFIG.write_kafka.topic_out} | "
            f"message: {message_data} | headers: {new_headers} | key: {key!r}",
        )

        await broker.publish(
            message=message_data,
            topic=CONFIG.write_kafka.topic_out,
            headers=new_headers,
            key=key,
        )

    async def publish_scope(
        self,
        call_next: Callable[[PublishCommand], Awaitable[Any]],
        cmd: PublishCommand,
    ) -> Any:
        return await call_next(cmd)
