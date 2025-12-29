import logging

from app.core.logger.context_storage import message_headers, message_key, request_id, stages_context


class RequestIdFilter(logging.Filter):
    """Добавляет request_id в запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


class StagesFilter(logging.Filter):
    """Добавляет stages в запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.stages = stages_context.get()
        return True


class MessageHeadersFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.message_headers = message_headers.get()
        return True


class MessageKeyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.message_key = message_key.get()
        return True
