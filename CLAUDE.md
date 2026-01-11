# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run Commands

### Setup
```bash
pip install uv
uv sync --no-install-project --all-groups
```

### Running the Application

**FastStream worker (Kafka consumer):**
```bash
uv run uvicorn app.service_main:app --host 0.0.0.0 --port 8080 --log-level warning
# or with CLI
uv run faststream run app.service_main:app --host 0.0.0.0 --port 8080
```

**FastAPI web server:**
```bash
uv run uvicorn app.web_main:app --host 0.0.0.0 --port 8080 --reload
```

**RAG pipeline locally (without Kafka):**
```bash
uv run python -m app.services.RAG.local_runner
```

### Testing
```bash
uv run pytest                           # Run all tests
uv run pytest tests/api/test_endpoints.py  # Single file
uv run pytest -k "test_name"            # Single test by name
```

### Linting and Formatting
```bash
uv run ruff check app/                  # Lint
uv run ruff check app/ --fix            # Lint with autofix
uv run black app/                       # Format
uv run isort app/                       # Sort imports
uv run mypy app/                        # Type checking
uv run pre-commit run --all-files       # All checks
```

### Docker
```bash
docker-compose up -d                    # Start Kafka, Langfuse, Redis, etc.
```

## Architecture

This is a **RAG (Retrieval-Augmented Generation) service** built with LangGraph, featuring two entry points:

### Entry Points
- `app/web_main.py` - FastAPI HTTP server with REST endpoints
- `app/service_main.py` - FastStream Kafka consumer (ASGI app)

### Core Components

**DependencyContainer** (`app/core/container.py`):
Manages lazy initialization of all RAG components. Creates: `AsyncLLM` → `RAGGraphBuilder` → `RAGPipeline` → `RagService`.

**RAG Pipeline** (`app/services/RAG/rag_pipeline/`):
LangGraph-based processing graph with nodes:
1. `IntentClassifier` - classifies user intent (FAQ/Support/General)
2. `RetrieverIntent` - reformulates query and retrieves documents
3. `DocsCounter` (Router) - conditional edge: stops if no docs found
4. `Reranker` - reorders documents by relevance
5. `BaseLLM` - generates response from context
6. `AnswerChecker` (optional) - validates response quality

**RAGState** (`app/services/RAG/rag_pipeline/state.py`):
TypedDict passed between graph nodes containing `messages`, `retrieved` docs, and `intent`.

**RAGGraphBuilder** (`app/services/RAG/rag_pipeline/graph/builder.py`):
Constructs and compiles the LangGraph StateGraph. Use `build()` for compiled graph, `get_image_graph()` for visualization.

### Configuration
All config via environment variables with `pydantic-settings`. Main config object: `CONFIG` from `app/core/config.py`. Nested configs use `__` delimiter (e.g., `API__PORT=8080`).

### Monitoring Stack
- Prometheus metrics at `/metrics`
- Langfuse for LLM tracing (v3, requires ClickHouse + Redis + Minio)
- Grafana dashboards: FastAPI (ID: 16110), FastStream (ID: 22130)

### Kafka Integration
- Consumer topic: `CONFIG.read_kafka.topic_in`
- Producer topic: `CONFIG.write_kafka.topic_out`
- Messages: `LangchainConsumerMessage` / `LangchainProducerMessage`
- AutoPublishMiddleware handles response publishing

## Adding New RAG Nodes

1. Create node class inheriting from `BaseNode` in `app/services/RAG/rag_pipeline/nodes/`
2. Implement `async def ainvoke(self, state: RAGState) -> dict` returning state updates
3. Register in `RAGGraphBuilder._build_graph()` with `builder.add_node()` and `builder.add_edge()`
4. Add prompts to `app/services/RAG/rag_pipeline/utils/prompts/prompts.py`

## Code Style Rules

- Весь интерфейс, комментарии и документация — на русском языке
- Логи на русском с emoji-префиксами: ✅ успех, ❌ ошибка, 🔧 инициализация, 🚀 запуск, 💤 остановка, ⏳ ожидание, под остальные логи подбирай подходящие смайлы
- Используй `logger = logging.getLogger(__name__)` в каждом модуле
- Line length: 120 символов (настроено в ruff/black)
- Async-first: все I/O операции через async/await
- Типизация обязательна для публичных методов и возвращаемых значений
- Для скрейпинга веб-страниц — используй `firecrawl-mcp` или похожий MCP
- Запускай код через виртуальную среду (`source .venv/bin/activate` или `uv run`)

## Принципы разработки

- Чем меньше строк кода — тем лучше
- Не удаляй существующие комментарии без причины
- Код должен быть понятен Junior-разработчику
- Предлагай простые и эффективные решения
- Акцент на результате, а не на количестве написанного

## Логика работы

- Используй `sequential-thinking` MCP для сложных размышлений
- Разбивай задачи на шаги, анализируй каждую часть перед принятием решения
- Проверяй совместимость, типы, сигнатуры функций до внесения изменений
- При работе с библиотеками/API — обращайся к `Context7` MCP за актуальной документацией


## Project Conventions

- Pydantic модели конфигов наследуют от `Config` с `SettingsConfigDict`
- Переменные окружения с префиксами: `API__`, `READ_KAFKA__`, `WRITE_KAFKA__`, `TSLG__`, etc.
- Kafka сообщения описываются через схемы в `app/core/kafka_broker/schemas.py`
- Промпты для LLM хранятся централизованно в `rag_pipeline/utils/prompts/`
- Ленивая инициализация компонентов через `@property` в `DependencyContainer`

## Imports Order

```python
# 1. Standard library
import logging
from typing import Any

# 2. Third-party
from fastapi import FastAPI
from langchain_core.messages import BaseMessage

# 3. Local (app.*)
from app.core.config import CONFIG
from app.services.RAG.rag_pipeline.state import RAGState
```

## Error Handling

- Используй кастомные исключения из `app/core/exceptions.py` и `app/services/RAG/exceptions.py`
- Логируй ошибки с полным контекстом: `logger.error(f"❌ Описание: {exc=!r}")`
- В lifespan оборачивай критические операции в try/except с логированием
