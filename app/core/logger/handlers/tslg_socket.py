import json
import logging
import socket
import struct
import uuid
from datetime import datetime, timezone
from logging.handlers import SocketHandler

from app.core.logger.utils import is_valid_uuid
from rnd_connectors.tslg.protocols import TSLGConfigProtocol
from rnd_connectors.tslg.schemas import TSLGMsgSchemas


class TslgSocketHandler(SocketHandler):
    """TCP Socket Handler для отправки JSON логов в TSLG Agent."""

    def __init__(self, config: TSLGConfigProtocol):
        self.tslg_config = config
        self._host = socket.gethostname()
        self._pod_ip = socket.gethostbyname(self._host)

        super().__init__(host=self.tslg_config.host, port=self.tslg_config.port)

    def makePickle(self, record: logging.LogRecord) -> bytes:
        """Преобразует LogRecord в JSON байты (вместо pickle)."""
        # """Преобразует LogRecord в JSON байты (вместо pickle)."""
        # message = self.format(record) + "\n"
        # return message.encode("utf-8")

        if record.exc_info:
            # just to get traceback text into record.exc_text ...
            self.format(record)

        # Временная метка в формате ISO 8601 с миллисекундами. Формат: 'YYYY‑MM‑ddTHH:mm:ss.SSSZ'
        dt = datetime.fromtimestamp(record.created, timezone.utc)
        time_create_log = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        request_id = getattr(record, "message_id", None)
        # request_id = getattr(record, "message_headers", {}).get("messageId")
        trace_id_header = getattr(record, "message_headers", {}).get("correlationId")
        trace_id = uuid.UUID(trace_id_header).hex if is_valid_uuid(trace_id_header) else None
        span_id = uuid.UUID(request_id).hex if is_valid_uuid(request_id) else None
        event_id = request_id if is_valid_uuid(request_id) else str(uuid.uuid4())

        msg_tslg = TSLGMsgSchemas(
            appName=self.tslg_config.app_name,
            appType=self.tslg_config.app_type,
            risCode=self.tslg_config.ris_code,
            projectCode=self.tslg_config.project_code,
            level=str(logging.getLevelName(record.levelno)),
            text=record.getMessage(),
            callerMethod=f"{record.filename}.{record.funcName}",
            callerLine=record.lineno,
            PID=record.process,
            stack=record.exc_text,
            eventId=str(event_id),
            localTime=time_create_log,
            podName=self._pod_ip,
            hostName=self._host,
            tec={"podIp": self._pod_ip},
            traceId=trace_id,
            spanId=span_id,
            tslgClientVersion=self.tslg_config.client_version,
            namespace=self.tslg_config.namespace,
            envType=self.tslg_config.env_type,
            loggerName=record.name,
            agrType=self.tslg_config.aggregation_type,
        )
        # msg_tslg есть возможность кодировать как в библиотеке в байты
        msg_encode_json = json.dumps(msg_tslg.model_dump(exclude_none=True)).encode("utf-8")
        length_bin = struct.pack(">I", len(msg_encode_json))

        return length_bin + msg_encode_json
