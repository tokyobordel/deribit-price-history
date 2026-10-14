# Deribit Price Service

Сервис для периодического получения индексных цен **BTC/USD** и **ETH/USD** с криптобиржи [Deribit](https://www.deribit.com/), сохранения истории в PostgreSQL и предоставления данных через REST API на FastAPI.

## Возможности

- Получение индексных цен `btc_usd` и `eth_usd` через публичный API Deribit.
- Автоматический сбор каждой цены **раз в минуту** с помощью Celery Beat и Celery Worker.
- Хранение тикера, цены и времени получения в PostgreSQL; время записывается как UNIX timestamp в секундах.
- Три GET-эндпоинта: полная история, последняя цена и цены за указанную дату.
- Валидация запросов и ответов с помощью Pydantic.
- Миграции схемы БД через Alembic и автоматическое применение при запуске Docker Compose.
- Модульные тесты и интеграционные тесты репозитория на PostgreSQL.

## Технологии

| Компонент | Технология |
| --- | --- |
| Язык | Python 3.12 (поддерживается Python 3.11+) |
| HTTP API | FastAPI, Uvicorn, Pydantic 2 |
| HTTP-клиент биржи | HTTPX |
| База данных | PostgreSQL, SQLAlchemy 2, psycopg 3 |
| Миграции | Alembic |
| Периодические задачи | Celery, Celery Beat |
| Брокер сообщений | Redis |
| Тесты | pytest, FastAPI TestClient, HTTPX MockTransport |
| Развёртывание | Docker, Docker Compose |

## Быстрый запуск через Docker Compose

**Требования:** Docker с поддержкой команды `docker compose`. Для работы сервиса необходим исходящий HTTPS-доступ к Deribit.

1. Подготовьте переменные окружения:

   ```bash
   cp .env.example .env
   ```

   Проверьте значение `POSTGRES_PASSWORD`. Для локальной разработки пример использует `deribit_dev`. Значения `DATABASE_URL` и `TEST_DATABASE_URL` для запуска из терминала должны содержать тот же пароль.

2. Соберите и запустите приложение:

   ```bash
   docker compose up -d --build
   ```

   Docker Compose запустит PostgreSQL и Redis, дождётся готовности PostgreSQL, выполнит миграции через одноразовый сервис `migrate`, затем запустит API, Worker и Beat.

3. Проверьте состояние сервисов:

   ```bash
   docker compose ps --all
   ```

   `postgres`, `redis`, `api`, `worker`, `beat` должны работать; для `migrate` нормальное состояние — `Exited (0)`.

4. Откройте Swagger UI: **http://127.0.0.1:8000/docs**.

5. Посмотрите последнюю сохранённую цену:

   ```bash
   curl "http://127.0.0.1:8000/api/prices/latest?ticker=btc_usd"
   ```

   До первого успешного сбора цена может отсутствовать, и API вернёт `404`.

### Сервисы Docker Compose

| Сервис | Назначение | Порт хоста |
| --- | --- | --- |
| `postgres` | Основная база данных | `127.0.0.1:5433` |
| `redis` | Брокер Celery | `127.0.0.1:6380` |
| `migrate` | Однократное выполнение `alembic upgrade head` | — |
| `api` | HTTP API | `127.0.0.1:8000` |
| `worker` | Выполнение задач сбора | — |
| `beat` | Постановка задач по расписанию | — |

## Конфигурация

Настройки считываются из переменных окружения; при локальном запуске `pydantic-settings` читает `.env` из рабочего каталога проекта.

Пример `.env` для разработки на хост-машине:

```dotenv
POSTGRES_PASSWORD=deribit_dev
DATABASE_URL=postgresql+psycopg://deribit:deribit_dev@localhost:5433/deribit_prices
TEST_DATABASE_URL=postgresql+psycopg://deribit:deribit_dev@localhost:5433/deribit_prices_test
CELERY_BROKER_URL=redis://localhost:6380/0
DERIBIT_BASE_URL=https://www.deribit.com/api/v2/
DERIBIT_TIMEOUT=10
```

## HTTP API

Все эндпоинты используют обязательный query-параметр `ticker` со значением `btc_usd` или `eth_usd`. Другие тикеры на данный момент не поддерживаются.

Интерактивная документация: **http://127.0.0.1:8000/docs**. Спецификация OpenAPI: **http://127.0.0.1:8000/openapi.json**.

### `GET /api/prices` — полная история

```bash
curl "http://127.0.0.1:8000/api/prices?ticker=btc_usd"
```

Пример ответа (`200 OK`):

```json
[
  {"ticker": "btc_usd", "price": "67500.25", "timestamp": 1791961427},
  {"ticker": "btc_usd", "price": "67501.10", "timestamp": 1791961487}
]
```

Записи возвращаются по возрастанию времени; если записей нет, возвращается `[]`.

### `GET /api/prices/latest` — последняя цена

```bash
curl "http://127.0.0.1:8000/api/prices/latest?ticker=eth_usd"
```

Пример ответа (`200 OK`):

```json
{"ticker": "eth_usd", "price": "3500.50", "timestamp": 1791961427}
```

Если для тикера пока нет данных, возвращается `404 Not Found`.

### `GET /api/prices/by-date` — история за дату

Дополнительный обязательный параметр `date` — дата в формате `YYYY-MM-DD`. Дата интерпретируется **по UTC**.

```bash
curl "http://127.0.0.1:8000/api/prices/by-date?ticker=btc_usd&date=2026-10-14"
```

Успешный ответ — массив объектов того же формата, что у `/api/prices`; при отсутствии записей возвращается `[]`. Отбор производится по интервалу от `00:00:00 UTC` указанной даты (включительно) до `00:00:00 UTC` следующей даты (исключительно).

## Периодический сбор данных

Celery Beat на каждой границе минуты ставит **две независимые задачи**: для `btc_usd` и `eth_usd`. Задачи передаются через Redis и выполняются Celery Worker. Каждая задача:

1. Валидирует входное сообщение (`CollectPriceTaskRequest`).
2. Запрашивает индексную цену через `GET /api/v2/public/get_index_price` Deribit с `index_name=<ticker>`.
3. Создаёт доменную сущность `Price`, фиксируя время получения ответа в UNIX timestamp.
4. Сохраняет запись через репозиторий SQLAlchemy внутри транзакции PostgreSQL.
5. После успешного `commit` пишет сообщение в лог.

Для получения публичной индексной цены авторизация Deribit не требуется.

При временных ошибках сети, HTTP `429`/`5xx` и `OperationalError` PostgreSQL выполняется до **трёх повторных попыток** с экспоненциальной задержкой. Для некорректного тикера, нарушения контракта ответа и остальных HTTP `4xx` автоматические повторы не предусмотрены. Результаты задач в брокере отдельно не сохраняются.

## Миграции Alembic

При запуске всей системы через Docker Compose миграции применяет сервис `migrate`.

## Тестирование

```bash
# Все тесты; требуется доступная тестовая PostgreSQL
python -m pytest -v

# Только модульные / HTTP-тесты, без PostgreSQL
python -m pytest -v -m "not integration"

# Только интеграционные тесты репозитория
python -m pytest -v -m integration
```

Интеграционные тесты используют **отдельную** БД из `TEST_DATABASE_URL`. Она должна отличаться от `DATABASE_URL`; тестовый набор проверяет это условие, чтобы исключить случайное изменение основной базы.

При первом запуске создайте тестовую БД (один раз):

```bash
docker compose exec postgres \
  psql -U deribit -d postgres \
  -c "CREATE DATABASE deribit_prices_test OWNER deribit;"
```

Примените к ней миграции:

```bash
DATABASE_URL='postgresql+psycopg://deribit:deribit_dev@localhost:5433/deribit_prices_test' \
  python -m alembic upgrade head
```

В этой команде указан пароль из примера конфигурации: при изменении `POSTGRES_PASSWORD` используйте свои актуальные данные подключения.

Модульные тесты используют моки источника цен и репозитория; тесты HTTP API переопределяют зависимости FastAPI; тесты репозитория выполняются на настоящей PostgreSQL с откатом тестовых транзакций. Тесты задач проверяют контракт сообщений, расписание и сборку зависимостей без запуска брокера.

## Архитектура

Проект разделён на слои, чтобы бизнес-логика не зависела от HTTP-фреймворка, клиента конкретной биржи или ORM.

```text
app/
├── api/
│   ├── dependencies.py       # Создание зависимостей FastAPI
│   ├── prices.py             # HTTP-эндпоинты
│   └── schemas.py            # Контракты публичного API
├── core/
│   ├── config.py             # Настройки из окружения
│   └── database.py           # SQLAlchemy Engine и Session
├── domain/
│   ├── entities.py           # Price
│   ├── interfaces.py         # PriceProvider, PriceRepository
│   └── tickers.py            # Ticker (StrEnum)
├── infrastructure/
│   ├── deribit/
│   │   ├── client.py         # DeribitClient
│   │   ├── contracts.py      # Схемы запросов/ответов Deribit
│   │   └── exceptions.py     # Ошибки интеграции
│   └── persistence/
│       ├── models.py         # PriceModel (SQLAlchemy)
│       └── price_repository.py
├── services/
│   ├── interfaces.py         # Контракты сервисов
│   ├── price_collection.py   # Сбор и сохранение цены
│   └── price_query.py        # Чтение истории и фильтрация
├── workers/
│   ├── celery_app.py         # Настройки и расписание Celery
│   ├── contracts.py          # Контракт сообщения задачи
│   └── tasks.py              # Обработчик Celery
└── main.py                   # FastAPI application factory
```

Компоненты сервисного слоя работают через интерфейсы `Protocol`. Адаптеры Deribit и SQLAlchemy реализуют доменные интерфейсы; FastAPI зависит от интерфейса сервиса. Сессия БД и HTTP-клиент создаются на границе выполнения запроса или задачи.

## Design decisions

| Решение | Обоснование |
| --- | --- |
| Доменные сущности отдельно от ORM | `Price` не зависит от SQLAlchemy, модели таблиц или инфраструктуры. |
| Общий `Ticker` как `StrEnum` | Единый набор поддерживаемых валют во всех слоях приложения. |
| Контракты на Pydantic | Проверка входящих сообщений, параметров API и ответа Deribit на границах системы. |
| Интерфейсы через `Protocol` | Зависимости сервисов можно заменять тестовыми реализациями без БД и сети. |
| Синхронные HTTP-клиент и SQLAlchemy | Для двух котировок в минуту асинхронный стек добавил бы сложность без практической необходимости; синхронные обработчики FastAPI работают в пуле потоков. |
| `Decimal` и PostgreSQL `NUMERIC` | Предотвращают ошибки двоичной арифметики `float` при хранении цен. |
| UNIX timestamp в секундах, UTC | Единое представление времени; фильтрация даты переводится в полуоткрытый интервал `[start, end)` по UTC. |
| Транзакции вне репозитория | Репозиторий выполняет операции с данными; вызывающий код управляет `commit`/`rollback`. |
| Celery Beat + Redis | Выполняют обязательное требование периодического сбора; задачи BTC и ETH независимы. |
| Ограниченные повторы задач | Временные ошибки сети, биржи и БД повторяются; ошибки контракта не маскируются бесконечными ретраями. |

## Известные ограничения и возможные улучшения

- **Нет восстановления пропущенных минут:** при простое брокера, планировщика, Worker или недоступности Deribit история за период сбоя не восполняется автоматически.
- **Локальные настройки не являются production-конфигурацией:** для внешнего развёртывания потребуются управление секретами, TLS, ограничение доступа к API и настройка мониторинга.
