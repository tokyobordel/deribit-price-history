
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.domain.entities import Price
from app.domain.tickers import Ticker


def test_create_price():
    price = Price(
        ticker=Ticker.BTC_USD,
        price=Decimal("67500.25"),
        timestamp=1791961427,
    )

    assert price.ticker == Ticker.BTC_USD
    assert price.price == Decimal("67500.25")
    assert price.timestamp == 1791961427


@pytest.mark.parametrize(
    "invalid_price",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_invalid_price(invalid_price):
    with pytest.raises(ValueError):
        Price(
            ticker=Ticker.BTC_USD,
            price=invalid_price,
            timestamp=1791961427,
        )


def test_negative_timestamp():
    with pytest.raises(ValueError):
        Price(
            ticker=Ticker.ETH_USD,
            price=Decimal("3500"),
            timestamp=-1,
        )


def test_price_is_immutable():
    price = Price(
        ticker=Ticker.BTC_USD,
        price=Decimal("67500.25"),
        timestamp=1791961427,
    )

    with pytest.raises(FrozenInstanceError):
        price.price = Decimal("100")
