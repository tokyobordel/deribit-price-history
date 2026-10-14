
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.entities import Price
from app.domain.tickers import Ticker
from app.infrastructure.persistence.models import PriceModel
from app.infrastructure.persistence.price_repository import (
    SQLAlchemyPriceRepository,
)


pytestmark = pytest.mark.integration


@pytest.fixture
def repository():
    settings = get_settings()

    if not settings.test_database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    if settings.test_database_url == settings.database_url:
        pytest.fail("Test database must differ from application DB")

    engine = create_engine(settings.test_database_url)

    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            try:
                with Session(
                    bind=connection,
                    autoflush=False,
                ) as session:
                    # Очищаем данные только внутри тестовой транзакции
                    session.execute(delete(PriceModel))

                    yield SQLAlchemyPriceRepository(session)
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def make_price(
    ticker: Ticker,
    value: str,
    timestamp: int,
) -> Price:
    return Price(
        ticker=ticker,
        price=Decimal(value),
        timestamp=timestamp,
    )


def test_save_and_get_all(repository):
    first = make_price(Ticker.BTC_USD, "100.25", 1000)
    second = make_price(Ticker.BTC_USD, "200.50", 2000)

    repository.save(second)
    repository.save(first)

    result = repository.get_all(Ticker.BTC_USD)

    assert result == [first, second]


def test_get_latest(repository):
    first = make_price(Ticker.BTC_USD, "100", 1000)
    second = make_price(Ticker.BTC_USD, "200", 2000)

    repository.save(first)
    repository.save(second)

    result = repository.get_latest(Ticker.BTC_USD)

    assert result == second


def test_get_latest_empty(repository):
    result = repository.get_latest(Ticker.ETH_USD)

    assert result is None


def test_filter_by_ticker(repository):
    btc = make_price(Ticker.BTC_USD, "100", 1000)
    eth = make_price(Ticker.ETH_USD, "20", 1000)

    repository.save(btc)
    repository.save(eth)

    assert repository.get_all(Ticker.BTC_USD) == [btc]
    assert repository.get_all(Ticker.ETH_USD) == [eth]


def test_get_by_period(repository):
    prices = [
        make_price(Ticker.BTC_USD, "100", 1000),
        make_price(Ticker.BTC_USD, "200", 2000),
        make_price(Ticker.BTC_USD, "300", 3000),
    ]

    for price in prices:
        repository.save(price)

    result = repository.get_by_period(
        ticker=Ticker.BTC_USD,
        start_timestamp=1000,
        end_timestamp=3000,
    )

    assert result == prices[:2]


def test_invalid_period(repository):
    with pytest.raises(ValueError):
        repository.get_by_period(
            ticker=Ticker.BTC_USD,
            start_timestamp=3000,
            end_timestamp=1000,
        )
