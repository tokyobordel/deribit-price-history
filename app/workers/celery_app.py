
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings
from app.domain.tickers import Ticker
from app.workers.contracts import CollectPriceTaskRequest


settings = get_settings()

celery_app = Celery(
    "deribit_prices",
    broker=settings.celery_broker_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    # Временная зона
    timezone="UTC",
    enable_utc=True,

    # Формат сообщений
    task_serializer="json",
    accept_content=["json"],

    # Результаты задач через Redis не храним
    task_ignore_result=True,

    # Восстановление подключения к брокеру
    broker_connection_retry_on_startup=True,

    # Равномерная выдача задач процессам Worker
    worker_prefetch_multiplier=1,

    # Периодическое выполнение
    beat_schedule={
        f"collect-{ticker.value}-every-minute": {
            "task": "app.workers.collect_price",
            "schedule": crontab(minute="*"),
            "kwargs": CollectPriceTaskRequest(
                ticker=ticker,
            ).model_dump(mode="json"),
        }
        for ticker in Ticker
    },
)
