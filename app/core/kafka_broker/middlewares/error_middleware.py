from faststream import ExceptionMiddleware
from pydantic import ValidationError

from app.core.config import CONFIG
from app.core.kafka_broker.schemas import CodeError, HeadersTopikOut, StatusCode
from app.core.logger import get_logger
from app.core.logger.context_storage import message_headers, message_key, reset_request_context
# 
from app.services.rag_service import RagService as Service
# 


logger = get_logger(__name__)

exc_middleware = ExceptionMiddleware()


@exc_middleware.add_handler(Exception, publish=False)  # type: ignore[misc]
async def error_handler(exc: Exception) -> None:
    """
    Ловит исключения, логирует и публикует сообщение об ошибке с корректными headers и key.
    """
    from app.core.kafka_broker.brokers import broker

    logger.error(f"🚨 Обработано исключение: {repr(exc)}")
    logger.error(f"🚨 Тип исключения: {type(exc).__name__}")
    logger.exception(f"🚨 Детали: {str(exc)}")

    error_message: str | None = None
    status_code: int
    code_error: int

    if isinstance(exc, ValidationError):
        # Ошибка валидации Pydantic
        status_code = StatusCode.PROCESSING_ERROR
        code_error = CodeError.MESSAGE_VALIDATION_ERROR
        error_message = str(exc)
        logger.error(f"🚨 Ошибка валидации: {error_message}")

    elif isinstance(exc, ValueError) and "Пустое body" in str(exc):
        # Специальная обработка для пустого body
        status_code = StatusCode.PROCESSING_ERROR
        code_error = CodeError.MESSAGE_VALIDATION_ERROR
        error_message = "Сообщение имеет пустое тело"
        logger.error(f"🚨 Ошибка валидации: {error_message}")

    elif isinstance(exc, ValueError):
        # Ошибки валидации (Headers missing, etc)
        status_code = StatusCode.PROCESSING_ERROR
        code_error = CodeError.MESSAGE_VALIDATION_ERROR
        error_message = str(exc)
        logger.error(f"🚨 Ошибка: {error_message}")
    else:
        # fallback к общим кодам
        status_code = StatusCode.PROCESSING_ERROR
        code_error = CodeError.UNEXPECTED_ERROR
        error_message = None  # Детали в логах

    try:
        error_msg_obj = Service.create_error_message(
            status_code=StatusCode(status_code),
            code_error=CodeError(code_error),
            error_message=error_message,
        )
        error_msg = error_msg_obj.model_dump(exclude_none=True)

        base_headers = message_headers.get() or {}
        key = message_key.get()

        # меняем хедеры (если меняются)
        new_headers = HeadersTopikOut(
            requestId=base_headers.get("requestId") or "unknown",
        ).model_dump(exclude_none=True)

        logger.info(
            f"📤 ⚠️Отправка сообщения об ошибке | topic={CONFIG.write_kafka.topic_out} | "
            f"message: {error_msg} | headers: {new_headers} | key: {key!r}",
        )

        await broker.publish(
            topic=CONFIG.write_kafka.topic_out,
            message=error_msg,
            headers=new_headers,
            key=key,
        )

        logger.info("✅ ⚠️ Сообщение об ошибке опубликовано")

    except Exception as e:
        logger.exception(f"❌ Не удалось опубликовать ошибку: {e}")
    finally:
        reset_request_context()
