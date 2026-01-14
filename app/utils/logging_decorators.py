import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """
    Декоратор для логирования времени выполнения функции.
    Поддерживает как синхронные, так и асинхронные функции.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                logger.debug(f"🚀 Начало выполнения {func.__name__}")
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в {func.__name__}: {e}")
                raise
            finally:
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                logger.info(f"✅ Функция {func.__name__} выполнена за {elapsed:.4f} секунд")

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                logger.debug(f"🚀 Начало выполнения {func.__name__}")
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в {func.__name__}: {e}")
                raise
            finally:
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                logger.info(f"✅ Функция {func.__name__} выполнена за {elapsed:.4f} секунд")

        return sync_wrapper
