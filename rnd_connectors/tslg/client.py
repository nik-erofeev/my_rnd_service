from confluent_kafka import KafkaError, KafkaException, Message, Producer  # type: ignore


class KafkaProducerClient:
    """Kafka producer для отправки TSLG логов."""

    def __init__(
        self,
        config,
    ) -> None:
        self._topic = config.kafka_topic

        # todo: ВРМ
        # producer_config = {
        #     "bootstrap.servers": config.kafka_bootstrap_servers,
        #     "security.protocol": "SSL",
        #     "ssl.ca.location": config.kafka_cafile,
        #     "ssl.certificate.location": config.kafka_certfile,
        #     "ssl.key.location": config.kafka_keyfile,
        #     "ssl.key.password": config.kafka_password,
        # }
        # todo: локально
        producer_config = {
            "bootstrap.servers": config.kafka_bootstrap_servers,
            # "security.protocol": "SSL",
            # "ssl.ca.location": config.kafka_cafile,
            # "ssl.certificate.location": config.kafka_certfile,
            # "ssl.key.location": config.kafka_keyfile,
            # "ssl.key.password": config.kafka_password,
        }

        try:
            self._producer = Producer(producer_config)
            self._closed = False
        except KafkaException as e:
            # Use print to avoid рекурсию (logging бы триггернул этот хендлер ещё раз)
            print(f"Kafka Producer initialization failed: {e}", flush=True)
            raise

    def send(self, log_string: str, key: str | None = None) -> bool:
        if self._closed:
            print("Kafka Producer is closed, cannot send message", flush=True)
            return False

        try:
            self._producer.produce(
                topic=self._topic,
                value=log_string.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                callback=self._delivery_callback,
            )

            self._producer.poll(0)

            return True

        except BufferError:
            # Очередь producer заполнена — poll для освобождения места
            print("Kafka Producer queue full, polling...", flush=True)
            self._producer.poll(1)  # Poll with 1 second timeout
            return True

        except KafkaException as e:
            print(f"Kafka send failed: {e}", flush=True)
            return False

        except Exception as e:
            print(f"Unexpected error sending to Kafka: {e}", flush=True)
            return False

    def _delivery_callback(self, err: KafkaError | None, msg: Message) -> None:
        if err:
            print(f"Kafka message delivery failed: {err}", flush=True)

    def flush(self, timeout: float = 10.0) -> None:
        if not self._closed:
            try:
                # flush возвращает количество неотправленных сообщений
                remaining = self._producer.flush(timeout)
                if remaining > 0:
                    print(
                        f"Kafka flush timeout: {remaining} messages not delivered",
                        flush=True,
                    )
            except Exception as e:
                print(f"Kafka flush failed: {e}", flush=True)

    def close(self) -> None:
        if not self._closed:
            try:
                self.flush()
                self._closed = True
            except Exception as e:
                print(f"Kafka Producer close failed: {e}", flush=True)
