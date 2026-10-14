
from dataclasses import dataclass
from decimal import Decimal

from app.domain.tickers import Ticker


@dataclass(frozen=True, slots=True)
class Price:
    """Индексная цена валюты на определённый момент времени."""

    ticker: Ticker
    price: Decimal
    timestamp: int

    def __post_init__(self) -> None:
        if not self.price.is_finite() or self.price <= 0:
            raise ValueError("Цена не должна быть отрицательной")

        if self.timestamp < 0:
            raise ValueError("Timestamp не должен быть отрицательным")
