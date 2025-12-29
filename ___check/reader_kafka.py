import logging
import ssl
from dataclasses import dataclass
from json import loads
from typing import Any

from faststream import FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.message import KafkaMessage
from faststream.security import BaseSecurity

from app.core.config import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class KafkaConfig:
    brokers: list[str]
    cafile: str | None = None
    certfile: str | None = None
    keyfile: str | None = None
    password: str | None = None
    verify_hostname: bool = True  # SSL проверка hostname

    def get_security(self) -> BaseSecurity | None:
        """Создаёт BaseSecurity, если заданы SSL-файлы"""
        if not all((self.cafile, self.certfile, self.keyfile)):
            logger.info("Не заданы SSL-файлы. ")
            return None

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations(self.cafile)
        context.load_cert_chain(
            certfile=self.certfile,  # type: ignore
            keyfile=self.keyfile,
            password=self.password,
        )
        context.check_hostname = self.verify_hostname

        return BaseSecurity(ssl_context=context, use_ssl=True)


KAFKA_CONFIGS = {
    "ss": KafkaConfig(
        brokers=[
            "p0pimc-kfc001lk.region.vtb.ru:9092",
            "p0pimc-kfc002lk.region.vtb.ru:9092",
            "p0pimc-kfc003lk.region.vtb.ru:9092",
            "p0pimc-kfc004lk.region.vtb.ru:9092",
        ],
        cafile="2890_cert_kafka/kafka_1655.ssl-ca.pem",  # "certs/preprod/Root_CA.pem"
        certfile="2890_cert_kafka/kafka_1655.ssl-key.pem",  # "certs/preprod/cert.pem"
        keyfile="2890_cert_kafka/kafka_1655.ssl-key-rsa.pem",  # "certs/preprod/key.pem"
        password="123321",
    ),
    "pre": KafkaConfig(
        brokers=[
            "rrpimc-kfc009lk.test.vtb.ru:9092",
            "rrpimc-kfc008lk.test.vtb.ru:9092",
            "rrpimc-kfc007lk.test.vtb.ru:9092",
        ],
        cafile="2890_cert_kafka_predprod/kafka_1655.ssl-ca.pem",  # "certs/preprod/Root_CA.pem"
        certfile="2890_cert_kafka_predprod/kafka_1655.ssl-key.pem",  # "certs/preprod/cert.pem"
        keyfile="2890_cert_kafka_predprod/kafka_1655.ssl-key-rsa.pem",  # "certs/preprod/key.pem"
        password="123321",
    ),
    "local": KafkaConfig(
        brokers=["localhost:29092"],
        # Нет SSL — используется для локальной разработки
    ),
}

# === Выбор окружения ===
ENV = "local"  # Можно вынести в env: os.getenv("KAFKA_ENV", "local")
if ENV not in KAFKA_CONFIGS:
    raise ValueError(f"Неизвестное окружение Kafka: {ENV}")

kafka_config = KAFKA_CONFIGS[ENV]
security = kafka_config.get_security()

# === Создание брокера ===
broker = KafkaBroker(
    kafka_config.brokers,
    security=security,
)


@broker.subscriber(
    CONFIG.read_kafka.topic_in,
    auto_offset_reset=CONFIG.read_kafka.auto_offset_reset,
)
async def handle_msg(msg: KafkaMessage):
    # async def handle_msg(msg: Any):  # для запуска docs
    logger.info("чек msg")
    msg_data = loads(msg.body)
    logger.info("msg_data: %s", msg_data)
    logger.info("header: %s", msg.headers)
    logger.info("key: %s", msg.raw_message.key)  # type: ignore
    return None


app = FastStream(broker)


@app.after_startup
async def example_log_start():
    logger.info("🚀FastStream приложение запущено. Подключение к кафке установлено")


@app.on_shutdown
async def example_log_stop():
    logger.info("💤 FastStream приложение остановлено. Работа завершена")


# run consumer
# faststream run ___check.reader_kafka:app
# faststream run ___check.reader_kafka:app --reload

# docs
# faststream docs serve ___check.reader_kafka:app --host 0.0.0.0 --port 8088


if __name__ == "__main__":
    import asyncio

    asyncio.run(app.run())
