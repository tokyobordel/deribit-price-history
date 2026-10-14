
from datetime import date, datetime, time, timezone

from app.domain.entities import Price
from app.domain.interfaces import PriceRepositoryInterface
from app.domain.tickers import Ticker
from app.services.interfaces import PriceQueryServiceInterface


class PriceQueryService(PriceQueryServiceInterface):
    """Сервис чтения сохранённых индексных цен."""

    def __init__(self, repository: PriceRepositoryInterface):
        self._repository = repository

    def get_all(self, ticker: Ticker) -> list[Price]:
        """Получить всю историю цен валюты."""
        return self._repository.get_all(ticker)

    def get_latest(self, ticker: Ticker) -> Price | None:
        """Получить последнюю сохранённую цену."""
        return self._repository.get_latest(ticker)

    def get_by_date(
        self,
        ticker: Ticker,
        target_date: date,
    ) -> list[Price]:
        """Получить цены за календарный день по UTC."""

        start = datetime.combine(
            target_date,
            time.min,
            tzinfo=timezone.utc,
        )

        start_timestamp = int(start.timestamp())
        end_timestamp = start_timestamp + 86400

        return self._repository.get_by_period(
            ticker=ticker,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
