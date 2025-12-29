#!/bin/sh

# Определение переменных
KAFKA_HOST="kafka"
KAFKA_PORT="9092"
MAX_RETRIES=60
RETRY_INTERVAL=2

echo "🚀 Старт приложения ожидаем кафку..."

# Проверка доступности Kafka с таймаутом
echo "⏳ Ожидание запуска Kafka на $KAFKA_HOST:$KAFKA_PORT..."
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    if nc -z "$KAFKA_HOST" "$KAFKA_PORT" 2>/dev/null; then
        echo "✅ Kafka готова к работе $KAFKA_HOST:$KAFKA_PORT"
        break
    else
        retry_count=$((retry_count + 1))
        echo "⏳ Kafka пока недоступна (попытка  $retry_count/$MAX_RETRIES), повторяем ${RETRY_INTERVAL} секунд..."
        sleep $RETRY_INTERVAL
    fi
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "❌ Ошибка: Kafka не доступна $MAX_RETRIES попыток. Остановка."
    exit 1
fi

# Дополнительная пауза для стабилизации Kafka
echo "⏳ Ожидание стабилизации Kafka в течение дополнительных 5 секунд..."
sleep 5

# Запуск основного приложения
echo "🚀 Starting FastStream server..."
# FASTSTREAM (uvicorn)  probes
exec uvicorn app.service_main:app --host 0.0.0.0 --port 8080 --log-level info
# exec uvicorn app.service_main:app --host 0.0.0.0 --port 8080 --log-level warning
# FASTSTREAM cli
# exec faststream run app.service_main:app --host 0.0.0.0 --port 8080

# API
# exec uvicorn app.web_main:app --host 0.0.0.0 --port 8080