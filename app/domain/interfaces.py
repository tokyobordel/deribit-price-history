
from decimal import Decimal
from typing import Protocol

from app.domain.entities import Price
from app.domain.tickers import Ticker


class PriceProviderInterface(Protocol):
    """Контракт источника индексных цен."""

    def get_index_price(self, ticker: Ticker) -> Decimal:
        """Получить текущую индексную цену."""
        ...


class PriceRepositoryInterface(Protocol):
    """Контракт хранилища исторических цен."""

    def save(self, price: Price) -> None:
        """Сохранить цену."""
        ...

    def get_all(self, ticker: Ticker) -> list[Price]:
        """Получить все сохранённые цены валюты."""
        ...

    def get_latest(self, ticker: Ticker) -> Price | None:
        """Получить последнюю сохранённую цену."""
        ...

    def get_by_period(
        self,
        ticker: Ticker,
        start_timestamp: int,
        end_timestamp: int,
    ) -> list[Price]:
        """
        Получить цены за период.

        start_timestamp включительно.
        end_timestamp исключительно.
        """
        ...
