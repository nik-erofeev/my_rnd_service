from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import FastAPI, Request
from prometheus_client import Counter, Gauge, Histogram, Info
from starlette.middleware.base import BaseHTTPMiddleware

HTTP_STATUS_SERVER_ERROR_MIN = 500

REQUESTS_TOTAL = Counter(
    "fastapi_requests_total",
    "Общее число HTTP-запросов",
    ["method", "path", "app_name"],
)

RESPONSES_TOTAL = Counter(
    "fastapi_responses_total",
    "Общее число HTTP-ответов по статусам",
    ["path", "status_code", "app_name"],
)

REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Запросы в обработке",
    ["path", "app_name"],
)

REQUEST_DURATION = Histogram(
    "fastapi_requests_duration_seconds",
    "Длительность обработки HTTP-запросов",
    ["method", "path", "app_name"],
)

APP_INFO = Info("fastapi_app", "Информация о FastAPI приложении")
EXCEPTIONS_TOTAL = Counter(
    "fastapi_exceptions_total",
    "Количество исключений/ошибок 5xx",
    ["app_name"],
)


class _PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, app_name: str) -> None:
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ):  # type: ignore[override]
        raw_path = request.url.path
        # Используем шаблон маршрута (меньше кардинальность)
        route = request.scope.get("route")
        path = getattr(route, "path", raw_path)
        if path == "/metrics":
            return await call_next(request)

        method = request.method
        REQUESTS_IN_PROGRESS.labels(path=path, app_name=self.app_name).inc()
        start = time.perf_counter()
        had_exception = False
        try:
            response = await call_next(request)
            return response
        except Exception:
            had_exception = True
            raise
        finally:
            duration = time.perf_counter() - start
            REQUESTS_IN_PROGRESS.labels(
                path=path,
                app_name=self.app_name,
            ).dec()
            REQUESTS_TOTAL.labels(
                method=method,
                path=path,
                app_name=self.app_name,
            ).inc()
            # status_code доступен только после ответа
            status_code = getattr(
                locals().get("response", None),
                "status_code",
                500,
            )
            RESPONSES_TOTAL.labels(
                path=path,
                status_code=str(status_code),
                app_name=self.app_name,
            ).inc()

            if had_exception or int(status_code) >= HTTP_STATUS_SERVER_ERROR_MIN:
                EXCEPTIONS_TOTAL.labels(app_name=self.app_name).inc()
            REQUEST_DURATION.labels(
                method=method,
                path=path,
                app_name=self.app_name,
            ).observe(duration)


def setup_fastapi_metrics(app: FastAPI, app_name: str) -> None:
    """Включает кастомные метрики fastapi_* для совместимости с дашбордом.

    Метрики публикуются на том же `/metrics` эндпоинте, который уже отдаёт
    стандартные метрики через `prometheus-fastapi-instrumentator`.
    """
    APP_INFO.info({"app_name": app_name})
    # Инициализация счётчиков, чтобы серии существовали сразу
    EXCEPTIONS_TOTAL.labels(app_name=app_name).inc(0)
    app.add_middleware(_PrometheusMiddleware, app_name=app_name)
