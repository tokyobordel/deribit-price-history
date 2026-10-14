
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import Mock

import pytest
from celery.schedules import crontab
from pydantic import ValidationError

from app.domain.entities import Price
from app.domain.tickers import Ticker
from app.workers import tasks
from app.workers.celery_app import celery_app


def test_beat_schedule():
    schedule = celery_app.conf.beat_schedule

    assert len(schedule) == len(Ticker)

    for ticker in Ticker:
        entry = schedule[
            f"collect-{ticker.value}-every-minute"
        ]

        assert entry["task"] == "app.workers.collect_price"
        assert entry["kwargs"] == {"ticker": ticker.value}
        assert isinstance(entry["schedule"], crontab)


def test_collect_price_invalid_ticker():
    with pytest.raises(ValidationError):
        tasks.collect_price.run("invalid_ticker")


def test_collect_price_task(monkeypatch):
    http_client = object()
    session = object()
    provider = object()
    repository = object()

    expected_price = Price(
        ticker=Ticker.BTC_USD,
        price=Decimal("67500.25"),
        timestamp=1791961427,
    )

    service = Mock()
    service.collect.return_value = expected_price

    events = []

    @contextmanager
    def fake_http_client(**kwargs):
        events.append("http_open")
        try:
            yield http_client
        finally:
            events.append("http_close")

    @contextmanager
    def fake_transaction():
        events.append("transaction_begin")
        yield session
        events.append("transaction_commit")

    class FakeSessionFactory:
        def begin(self):
            return fake_transaction()

    monkeypatch.setattr(
        tasks.httpx,
        "Client",
        fake_http_client,
    )

    monkeypatch.setattr(
        tasks,
        "get_session_factory",
        lambda: FakeSessionFactory(),
    )

    monkeypatch.setattr(
        tasks,
        "DeribitClient",
        lambda client: provider,
    )

    monkeypatch.setattr(
        tasks,
        "SQLAlchemyPriceRepository",
        lambda db_session: repository,
    )

    monkeypatch.setattr(
        tasks,
        "PriceCollectionService",
        lambda provider, repository: service,
    )

    tasks.collect_price.run("btc_usd")

    service.collect.assert_called_once_with(
        Ticker.BTC_USD
    )

    assert events == [
        "http_open",
        "transaction_begin",
        "transaction_commit",
        "http_close",
    ]
