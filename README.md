# Payment Processing Service

Асинхронный микросервис процессинга платежей на FastAPI, PostgreSQL и RabbitMQ.

## Возможности

- создание платежа с защитой от повторного `Idempotency-Key`;
- получение текущего состояния платежа;
- transactional outbox для гарантированной публикации событий;
- асинхронная обработка через RabbitMQ и FastStream;
- эмуляция платёжного шлюза: 2–5 секунд, 90% успеха и 10% ошибки;
- webhook с результатом обработки;
- три попытки обработки с экспоненциальной задержкой;
- Dead Letter Queue для окончательно упавших сообщений;
- статическая авторизация через `X-API-Key`.

## Запуск

Для запуска требуется Docker с поддержкой Compose.

```bash
docker compose up --build
```

Compose поднимает:

- API: <http://localhost:8000>;
- Swagger UI: <http://localhost:8000/docs>;
- PostgreSQL: `localhost:5432`;
- RabbitMQ: `localhost:5672`;
- RabbitMQ Management: <http://localhost:15672> (`payment` / `payment`);
- consumer платежей;
- одноразовый сервис применения миграций.

API-ключ окружения Compose:

```text
development-api-key
```

Остановка:

```bash
docker compose down
```

Удаление контейнеров вместе с данными PostgreSQL:

```bash
docker compose down --volumes
```

## API

### Проверка доступности

```bash
curl http://localhost:8000/api/v1/health \
  -H 'X-API-Key: development-api-key'
```

### Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: development-api-key' \
  -H 'Idempotency-Key: payment-request-1' \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "Order payment",
    "metadata": {"order_id": "order-1"},
    "webhook_url": "https://example.com/payment-webhook"
  }'
```

Успешный ответ возвращается со статусом `202 Accepted`:

```json
{
  "payment_id": "7e95bd45-c72e-4c99-b36e-95c8a88d604a",
  "status": "pending",
  "created_at": "2026-10-05T12:00:00Z"
}
```

Повторный запрос с тем же `Idempotency-Key` возвращает ранее созданный платёж.

### Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/7e95bd45-c72e-4c99-b36e-95c8a88d604a \
  -H 'X-API-Key: development-api-key'
```

## Webhook

После процессинга сервис отправляет `POST` на переданный `webhook_url`:

```json
{
  "payment_id": "7e95bd45-c72e-4c99-b36e-95c8a88d604a",
  "status": "succeeded",
  "processed_at": "2026-10-05T12:00:04Z"
}
```

Webhook содержит заголовок:

```text
Idempotency-Key: payment-result:<payment_id>
```

## Переменные окружения

Локальный файл можно создать из примера:

```bash
cp .env.example .env
```

Основные настройки:

| Переменная | Назначение |
| --- | --- |
| `APP_API_KEY` | Статический ключ HTTP API |
| `APP_DB_HOST` | Адрес PostgreSQL |
| `APP_DB_PORT` | Порт PostgreSQL |
| `APP_DB_NAME` | Имя базы данных |
| `APP_DB_USER` | Пользователь PostgreSQL |
| `APP_DB_PASSWORD` | Пароль PostgreSQL |
| `APP_RABBITMQ_HOST` | Адрес RabbitMQ |
| `APP_RABBITMQ_PORT` | Порт RabbitMQ |
| `APP_RABBITMQ_USER` | Пользователь RabbitMQ |
| `APP_RABBITMQ_PASSWORD` | Пароль RabbitMQ |
| `APP_RABBITMQ_VHOST` | Virtual host RabbitMQ |

## Миграции

Применить миграции локально:

```bash
uv run alembic upgrade head
```

Создать новую миграцию:

```bash
uv run alembic revision --autogenerate -m "migration name"
```

## Тесты

```bash
uv run python -m unittest discover -s tests/unit -v
```

## Архитектура

```text
app/
├── domain/          # сущности, статусы и доменные события
├── application/     # use cases и порты
├── infrastructure/  # PostgreSQL, RabbitMQ, webhook
└── presentation/    # FastAPI и consumer
```

Создание платежа и outbox-события выполняется в одной транзакции PostgreSQL. Фоновый
publisher выбирает неопубликованные события через `FOR UPDATE SKIP LOCKED`, отправляет
их через exchange `payments.events` в очередь `payments.new` и после подтверждения
RabbitMQ устанавливает `published_at`.
