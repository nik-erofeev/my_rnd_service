import ssl
from typing import Any

from faststream.security import BaseSecurity

from app.core.config import CONFIG


def create_ssl_security() -> BaseSecurity | None:
    """Создает SSL конфигурацию для Kafka брокера."""
    if not CONFIG.read_kafka.use_ssl:
        print("SSL не используется для Kafka подключения")
        return None

    try:
        ssl_context = ssl.create_default_context()

        # Настройка проверки hostname
        ssl_context.check_hostname = CONFIG.read_kafka.ssl_check_hostname
        print(f"SSL check_hostname установлен: {CONFIG.read_kafka.ssl_check_hostname}")

        # Загрузка CA файла для проверки сертификата сервера
        if CONFIG.ssl_kafka.cafile:
            ssl_context.load_verify_locations(cafile=CONFIG.ssl_kafka.cafile)
            print(f"Загружен CA файл: {CONFIG.ssl_kafka.cafile}")

        # Загрузка клиентского сертификата для аутентификации
        if CONFIG.ssl_kafka.certfile and CONFIG.ssl_kafka.keyfile:
            ssl_context.load_cert_chain(
                certfile=CONFIG.ssl_kafka.certfile,
                keyfile=CONFIG.ssl_kafka.keyfile,
                password=CONFIG.ssl_kafka.password,
            )
            print(f"Загружен клиентский сертификат: {CONFIG.ssl_kafka.certfile}")

        print("SSL конфигурация успешно настроена с использованием ssl.SSLContext")

        return BaseSecurity(ssl_context=ssl_context)

    except Exception as e:
        print(f"Ошибка при настройке SSL конфигурации: {e}")
        raise


def ssl_and_update_broker_kwargs() -> dict[str, Any]:
    """Обогащает kwargs брокера security и additional_broker_config.

    Returns:
        dict: объединённые параметры
    """
    broker_kwargs: dict[str, Any] = {}

    ssl_security = create_ssl_security()
    if ssl_security is not None:
        broker_kwargs["security"] = ssl_security

    # Доп. параметры из конфига
    broker_kwargs.update(CONFIG.ssl_kafka.additional_broker_config)

    return broker_kwargs
