
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.domain.entities import Price
from app.domain.interfaces import PriceProviderInterface, PriceRepositoryInterface
from app.domain.tickers import Ticker
from app.services.price_collection import PriceCollectionService
from app.services.price_query import PriceQueryService


# --------------------------------------------------
# PriceCollectionService
# --------------------------------------------------

def test_collect_price():
    provider = Mock(spec=PriceProviderInterface)
    repository = Mock(spec=PriceRepositoryInterface)

    provider.get_index_price.return_value = Decimal("67500.25")

    service = PriceCollectionService(
        provider=provider,
        repository=repository,
        clock=lambda: 1791961427,
    )

    result = service.collect(Ticker.BTC_USD)

    expected = Price(
        ticker=Ticker.BTC_USD,
        price=Decimal("67500.25"),
        timestamp=1791961427,
    )

    assert result == expected

    provider.get_index_price.assert_called_once_with(
        Ticker.BTC_USD
    )

    repository.save.assert_called_once_with(expected)


def test_collect_provider_error():
    provider = Mock(spec=PriceProviderInterface)
    repository = Mock(spec=PriceRepositoryInterface)

    provider.get_index_price.side_effect = RuntimeError(
        "Provider unavailable"
    )

    service = PriceCollectionService(
        provider=provider,
        repository=repository,
        clock=lambda: 1791961427,
    )

    with pytest.raises(RuntimeError):
        service.collect(Ticker.BTC_USD)

    repository.save.assert_not_called()


# --------------------------------------------------
# PriceQueryService
# --------------------------------------------------

def test_query_get_all():
    repository = Mock(spec=PriceRepositoryInterface)

    prices = [
        Price(Ticker.BTC_USD, Decimal("100"), 1000),
        Price(Ticker.BTC_USD, Decimal("200"), 2000),
    ]

    repository.get_all.return_value = prices

    service = PriceQueryService(repository)

    result = service.get_all(Ticker.BTC_USD)

    assert result == prices

    repository.get_all.assert_called_once_with(
        Ticker.BTC_USD
    )


def test_query_get_latest():
    repository = Mock(spec=PriceRepositoryInterface)

    expected = Price(
        Ticker.ETH_USD,
        Decimal("3500.50"),
        2000,
    )

    repository.get_latest.return_value = expected

    service = PriceQueryService(repository)

    result = service.get_latest(Ticker.ETH_USD)

    assert result == expected

    repository.get_latest.assert_called_once_with(
        Ticker.ETH_USD
    )


def test_query_get_latest_empty():
    repository = Mock(spec=PriceRepositoryInterface)

    repository.get_latest.return_value = None

    service = PriceQueryService(repository)

    assert service.get_latest(Ticker.BTC_USD) is None


def test_query_get_by_date():
    repository = Mock(spec=PriceRepositoryInterface)
    repository.get_by_period.return_value = []

    service = PriceQueryService(repository)

    result = service.get_by_date(
        Ticker.BTC_USD,
        date(2026, 10, 14),
    )

    start = int(
        datetime(
            2026, 10, 14,
            tzinfo=timezone.utc,
        ).timestamp()
    )

    repository.get_by_period.assert_called_once_with(
        ticker=Ticker.BTC_USD,
        start_timestamp=start,
        end_timestamp=start + 86400,
    )

    assert result == []
