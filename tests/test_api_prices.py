
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_price_query_service
from app.domain.entities import Price
from app.domain.tickers import Ticker
from app.main import app
from app.services.interfaces import PriceQueryServiceInterface


@pytest.fixture
def api_client():
    service = Mock(spec=PriceQueryServiceInterface)

    app.dependency_overrides[get_price_query_service] = (
        lambda: service
    )

    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.pop(
            get_price_query_service, None
        )


def test_get_all_prices(api_client):
    client, service = api_client

    price = Price(
        ticker=Ticker.BTC_USD,
        price=Decimal("67500.25"),
        timestamp=1791961427,
    )

    service.get_all.return_value = [price]

    response = client.get(
        "/api/prices",
        params={"ticker": "btc_usd"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "ticker": "btc_usd",
            "price": "67500.25",
            "timestamp": 1791961427,
        }
    ]

    service.get_all.assert_called_once_with(
        Ticker.BTC_USD
    )


def test_get_all_prices_empty(api_client):
    client, service = api_client

    service.get_all.return_value = []

    response = client.get(
        "/api/prices",
        params={"ticker": "btc_usd"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_latest_price(api_client):
    client, service = api_client

    price = Price(
        ticker=Ticker.ETH_USD,
        price=Decimal("3500.50"),
        timestamp=1791961427,
    )

    service.get_latest.return_value = price

    response = client.get(
        "/api/prices/latest",
        params={"ticker": "eth_usd"},
    )

    assert response.status_code == 200
    assert response.json()["price"] == "3500.50"

    service.get_latest.assert_called_once_with(
        Ticker.ETH_USD
    )


def test_get_latest_price_not_found(api_client):
    client, service = api_client

    service.get_latest.return_value = None

    response = client.get(
        "/api/prices/latest",
        params={"ticker": "btc_usd"},
    )

    assert response.status_code == 404


def test_get_prices_by_date(api_client):
    client, service = api_client

    service.get_by_date.return_value = []

    response = client.get(
        "/api/prices/by-date",
        params={
            "ticker": "btc_usd",
            "date": "2026-10-14",
        },
    )

    assert response.status_code == 200
    assert response.json() == []

    service.get_by_date.assert_called_once_with(
        ticker=Ticker.BTC_USD,
        target_date=date(2026, 10, 14),
    )


def test_missing_ticker(api_client):
    client, service = api_client

    response = client.get("/api/prices")

    assert response.status_code == 422
    service.get_all.assert_not_called()


def test_invalid_ticker(api_client):
    client, service = api_client

    response = client.get(
        "/api/prices",
        params={"ticker": "ltc_usd"},
    )

    assert response.status_code == 422
    service.get_all.assert_not_called()


def test_invalid_date(api_client):
    client, service = api_client

    response = client.get(
        "/api/prices/by-date",
        params={
            "ticker": "btc_usd",
            "date": "invalid-date",
        },
    )

    assert response.status_code == 422
    service.get_by_date.assert_not_called()
