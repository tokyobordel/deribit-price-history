
from decimal import Decimal

import httpx
import pytest

from app.infrastructure.deribit.client import DeribitClient
from app.infrastructure.deribit.exceptions import (
    DeribitAPIError,
    DeribitProtocolError,
)
from app.domain.tickers import Ticker


def make_client(payload):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json=payload,
        )
    )

    return httpx.Client(
        base_url="https://test.deribit.com/api/v2/",
        transport=transport,
    )


def test_get_index_price_success():
    payload = {
        "jsonrpc": "2.0",
        "result": {
            "index_price": 67500.25,
            "estimated_delivery_price": 67500.25,
        },
    }

    with make_client(payload) as http:
        client = DeribitClient(http)

        price = client.get_index_price(Ticker("btc_usd"))

    assert price == Decimal("67500.25")


def test_deribit_api_error():
    payload = {
        "jsonrpc": "2.0",
        "error": {
            "code": 11050,
            "message": "bad_request",
        },
    }

    with make_client(payload) as http:
        client = DeribitClient(http)

        with pytest.raises(DeribitAPIError) as exc:
            client.get_index_price(Ticker("btc_usd"))

    assert exc.value.code == 11050


def test_invalid_response_contract():
    payload = {
        "jsonrpc": "2.0",
        "result": {
            "unexpected_field": 123
        },
    }

    with make_client(payload) as http:
        client = DeribitClient(http)

        with pytest.raises(DeribitProtocolError):
            client.get_index_price(Ticker("eth_usd"))
