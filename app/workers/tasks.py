
import logging

import httpx
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.infrastructure.deribit.client import DeribitClient
from app.infrastructure.persistence.price_repository import (
    SQLAlchemyPriceRepository,
)
from app.services.interfaces import (
    PriceCollectionServiceInterface,
)
from app.services.price_collection import PriceCollectionService
from app.workers.celery_app import celery_app
from app.workers.contracts import CollectPriceTaskRequest
from app.domain.tickers import Ticker

logger = logging.getLogger(__name__)


class RetryableDeribitHTTPError(Exception):
    """Временная HTTP-ошибка Deribit."""


@celery_app.task(
    name="app.workers.collect_price",
    autoretry_for=(
        httpx.RequestError,
        OperationalError,
        RetryableDeribitHTTPError,
    ),
    max_retries=3,
    retry_backoff=2,
    retry_backoff_max=30,
    retry_jitter=True,
    ignore_result=True,
)
def collect_price(ticker: str) -> None:
    """Получить и сохранить цену указанной валюты."""

    # Проверяем контракт сообщения
    request = CollectPriceTaskRequest.model_validate({
        "ticker": ticker,
    })

    settings = get_settings()

    try:
        # Создаём HTTP-клиент на время задачи
        with httpx.Client(
            base_url=settings.deribit_base_url,
            timeout=settings.deribit_timeout,
        ) as http_client:

            provider = DeribitClient(http_client)

            # Транзакция БД
            with get_session_factory().begin() as session:
                repository = SQLAlchemyPriceRepository(session)

                service: PriceCollectionServiceInterface = (
                    PriceCollectionService(
                        provider=provider,
                        repository=repository,
                    )
                )

                price = service.collect(request.ticker)

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        # Повторяем только временные HTTP-ошибки
        if status_code == 429 or 500 <= status_code < 600:
            raise RetryableDeribitHTTPError(
                f"Внешнее API вернуло статус {status_code}"
            ) from exc

        raise

    # Сюда попадаем только после успешного commit
    logger.info(
        "Данные сохранены: ticker=%s price=%s timestamp=%s",
        price.ticker.value,
        price.price,
        price.timestamp,
    )
