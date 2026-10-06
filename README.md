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

## Быстрый запуск

Для запуска требуется Docker с поддержкой Compose.

```bash
docker compose up --build
```

Первый запуск может занять несколько минут: Docker скачает образы и установит
Python-зависимости. Сервис готов, когда `api`, `consumer`, `postgres` и `rabbitmq`
имеют статус `Up`, а `migrations` завершился с кодом `0`:

```bash
docker compose ps -a
```

Compose поднимает:

- API: <http://localhost:8000>;
- Swagger UI: <http://localhost:8000/docs>;
- PostgreSQL: `localhost:5432`;
- RabbitMQ: `localhost:5672`;
- RabbitMQ Management: <http://localhost:15672> (`payment` / `payment`);
- consumer платежей;
- одноразовый сервис применения миграций.

Контейнер `migrations` со статусом `Exited (0)` — это нормальное состояние:
миграции были применены, после чего контейнер завершил работу.

Вручную создавать базу данных не требуется. При первом запуске контейнер PostgreSQL
автоматически создаёт базу `payment` и пользователя `payment` согласно настройкам
`POSTGRES_DB` и `POSTGRES_USER` в `compose.yml`. После успешного health check отдельный
контейнер `migrations` выполняет `alembic upgrade head` и создаёт таблицы `payments`,
`outbox` и служебную таблицу `alembic_version`. API и consumer запускаются только после
успешного завершения миграций.

Проверить созданные таблицы можно командой:

```bash
docker compose exec postgres psql -U payment -d payment -c '\dt'
```

Данные сохраняются в Docker volume `postgres-data` и не теряются после обычного
`docker compose down`.

API-ключ окружения Compose:

```text
development-api-key
```

Если один из портов уже занят, задайте другой хост-порт перед запуском. Внутренние
адреса контейнеров менять не нужно:

```bash
POSTGRES_PORT=5433 API_PORT=8080 docker compose up --build
```

В этом примере Swagger будет доступен на <http://localhost:8080/docs>, а PostgreSQL —
на `localhost:5433`. Аналогично поддерживаются `RABBITMQ_PORT` и
`RABBITMQ_MANAGEMENT_PORT`.

Остановка:

```bash
docker compose down
```

Удаление контейнеров вместе с данными PostgreSQL:

```bash
docker compose down --volumes
```

Команда с `--volumes` удаляет локальные данные PostgreSQL без возможности
восстановления. Для обычной остановки используйте `docker compose down`.

## Проверка полного сценария

### 1. Health check

```bash
curl -i http://localhost:8000/api/v1/health \
  -H 'X-API-Key: development-api-key'
```

Ожидается `HTTP/1.1 200 OK` и `{"status":"ok"}`. Без `X-API-Key` API вернёт
`401 Unauthorized`.

### 2. Подготовка webhook

Для ручной проверки удобно создать временный URL на <https://webhook.site> и
подставить его вместо `https://your-unique-url.webhook.site` в следующую команду.
После обработки платежа входящий запрос появится на странице webhook.site.

Если внешний webhook не нужен, можно указать любой валидный URL. Платёж всё равно
будет обработан и сохранён, но consumer сделает три попытки уведомления и отправит
сообщение в `payments.dlq`, если URL недоступен.

### 3. Создание платежа

```bash
curl -i -X POST http://localhost:8000/api/v1/payments \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: development-api-key' \
  -H 'Idempotency-Key: order-1001-payment' \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "Order 1001",
    "metadata": {"order_id": "1001"},
    "webhook_url": "https://your-unique-url.webhook.site"
  }'
```

API сразу вернёт `202 Accepted`, идентификатор и начальный статус `pending`. Скопируйте
значение `payment_id` из ответа.

### 4. Получение результата

Обработка занимает 2–5 секунд. Подставьте полученный UUID:

```bash
curl http://localhost:8000/api/v1/payments/<payment_id> \
  -H 'X-API-Key: development-api-key'
```

Статус сменится на `succeeded` (вероятность 90%) или `failed` (10%), а
`processed_at` перестанет быть `null`. Оба статуса являются штатным результатом
эмуляции платёжного шлюза.

Webhook получит такой JSON и заголовок
`Idempotency-Key: payment-result:<payment_id>`:

```json
{
  "payment_id": "683b8189-8400-4b8b-8725-7fe0071588e7",
  "status": "succeeded",
  "processed_at": "2026-10-06T06:58:50.773128+00:00"
}
```

### 5. Проверка идемпотентности

Повторите `POST` с тем же `Idempotency-Key`. Ответ должен содержать тот же
`payment_id`; новая строка платежа и новое outbox-событие не создаются.

### 6. Проверка инфраструктуры

```bash
docker compose logs -f api consumer
```

В логе consumer для успешного сообщения будут строки `Received` и `Processed`.
Очереди можно посмотреть в RabbitMQ Management на <http://localhost:15672>:

- логин: `payment`;
- пароль: `payment`;
- рабочая очередь: `payments.new`;
- очередь окончательно упавших сообщений: `payments.dlq`.

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
uv sync --dev
uv run pytest -q
uv run ruff check .
uv run mypy app
```

Ожидаемый результат тестов: `15 passed`.

## Диагностика

- `port is already allocated` — задайте свободный порт, например
  `POSTGRES_PORT=5433 docker compose up --build`.
- API не отвечает — проверьте `docker compose ps -a` и
  `docker compose logs api`.
- Платёж остаётся `pending` — проверьте `docker compose logs consumer rabbitmq`.
- Платёж обработан, но webhook не пришёл — consumer повторяет HTTP-запрос три раза
  с задержками 1 и 2 секунды; затем сообщение попадает в `payments.dlq`.
- Полностью начать заново — выполните `docker compose down --volumes`, затем
  `docker compose up --build`. Это удалит существующие локальные платежи.

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

Путь запроса целиком:

```text
POST /payments
  -> PostgreSQL: payment + outbox в одной транзакции
  -> outbox publisher
  -> RabbitMQ: payments.events -> payments.new
  -> consumer: эмуляция шлюза -> обновление payment
  -> HTTP webhook
  -> при трёх неудачных попытках: payments.dlq
```
