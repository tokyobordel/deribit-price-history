
from datetime import date
from typing import Protocol

from app.domain.entities import Price
from app.domain.tickers import Ticker


class PriceCollectionServiceInterface(Protocol):
    """Контракт сервиса сбора цен."""

    def collect(self, ticker: Ticker) -> Price:
        """Получить актуальную цену и сохранить её."""
        ...


class PriceQueryServiceInterface(Protocol):
    """Контракт сервиса получения сохранённых цен."""

    def get_all(self, ticker: Ticker) -> list[Price]:
        """Получить все цены валюты."""
        ...

    def get_latest(self, ticker: Ticker) -> Price | None:
        """Получить последнюю сохранённую цену."""
        ...

    def get_by_date(
        self,
        ticker: Ticker,
        target_date: date,
    ) -> list[Price]:
        """Получить цены за календарный день по UTC."""
        ...
