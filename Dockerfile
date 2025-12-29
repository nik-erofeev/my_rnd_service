FROM python:3.13-slim
# https://docs.astral.sh/uv/guides/integration/docker/#installing-a-project

# ✅ 1. Настройка переменных окружения
# Добавляем путь к venv в PATH, чтобы uvicorn был доступен сразу
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# уточнить за
#UV_COMPILE_BYTECODE=1 \
#UV_LINK_MODE=copy \

WORKDIR /app
RUN chmod -R 777 /app



# ✅ 2.  Системные зависимости
RUN apt-get update && \
    apt-get install -y \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ✅ 3. Установить uv
RUN pip install --no-cache-dir uv

# requirements
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
# UV
# Ставим зависимости прямо в системный Python контейнера (доп) - плохо
# RUN #uv pip install --system --no-cache .

# ✅ 4. Копируем ТОЛЬКО манифесты (слой кеша)
#COPY pyproject.toml uv.lock ./
COPY pyproject.toml ./

# ✅ 5. Установить зависимости БЕЗ проекта (кешируется отдельно)
# --frozen: гарантирует, что uv не будет пытаться обновить lock-файл - если есть
# --no-install-project: не устанавливает сам текущий проект (только зависимости)
# т.к. код мы скопируем позже.
# --all-groups: устанавливает все группы зависимостей
# RUN uv sync --frozen --no-install-project --all-groups
RUN uv sync --no-install-project --all-groups


# ✅ 6. Копируем ВСЕ папки проекта (правильно!)
#COPY . .
# ✅ Правильно: копируем ПАПКУ в ПАПКУ
COPY app/ ./app/
COPY rnd_connectors/ ./rnd_connectors/
COPY tests/ ./tests/


# Открываем порт (если приложение использует HTTP)
#EXPOSE 8080


# ✅ 7. Запуск (app.sh)
COPY app.sh ./
# Устанавливаем права на выполнение для скриптов
RUN chmod +x /app/*.sh
# Запускаем через app.sh скрипт
CMD ["/app/app.sh"]



# ✅ 7. Запуск(dockerfile)
# RUN sleep 30 # мок ожидание перед кафкой
# API
#CMD ["uvicorn", "app.web_main:app", "--host", "0.0.0.0", "--port", "8080"]

# faststream(service) - uvicorn чтобы задавть уровень логов (игнорировать probes)
#CMD ["uvicorn", "app.service_main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
#CMD ["uvicorn", "app.service_main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "warning"]

# faststream
#CMD ["faststream", "run", "app.service_main:app", "--host", "0.0.0.0", "--port", "8080"]