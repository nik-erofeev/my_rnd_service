import logging
import random
import ssl
from dataclasses import dataclass
from uuid import uuid4

from faststream import FastStream
from faststream.kafka import KafkaBroker
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
            certfile=self.certfile,
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


app = FastStream(broker)


def generate_message():
    request_id = str(random.randint(1, 9999))
    trace_id = str(random.randint(1, 9999))

    # headers = ConsumerHeaders(traceId=trace_id, requestId=request_id).model_dump()
    headers = {
        "traceId": request_id,
        "requestId": trace_id,
        # "asd": "123",
    }

    # query = "какая погода в Москве?"
    query = "Какие документы нужны для оформления ипотеки?"

    msg = {"test_questions": query}

    return msg, headers


async def send_test_message():
    try:

        message, headers = generate_message()

        await broker.publish(
            message=message,
            # message=None,
            topic="topic-in-test",
            headers=headers,
            key=b"test_key1",
        )
        logger.info(f"Контур: {ENV}")
        logger.info(f"Сообщение успешно отправлено в топик topic-in-test")
    except Exception as e:
        logger.exception(f"Ошибка при отправке сообщения в топик: {e}")


async def send_messages_multiple_times(count: int):

    await broker.connect()
    # while True:
    #     await asyncio.sleep(1)
    tasks = [send_test_message() for _ in range(count)]
    await asyncio.gather(*tasks)
    logger.info(f"Отправлено сообщений: {len(tasks)}")

    await broker.stop()


if __name__ == "__main__":
    import asyncio

    cnt = 1
    asyncio.run(send_messages_multiple_times(count=cnt))
