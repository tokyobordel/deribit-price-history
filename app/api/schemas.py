import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.tickers import Ticker


class TickerQueryParams(BaseModel):
    """Query-параметры запроса цен."""

    model_config = ConfigDict(extra="forbid")

    ticker: Ticker = Field(
        description="Тикер валютного индекса",
    )


class PricesByDateQueryParams(TickerQueryParams):
    """Query-параметры запроса цен за дату."""

    date: dt.date = Field(
        description="Календарная дата по UTC",
    )


class PriceResponse(BaseModel):
    """Публичный контракт сохранённой цены."""

    model_config = ConfigDict(from_attributes=True)

    ticker: Ticker = Field(
        description="Тикер валютного индекса",
    )

    price: Decimal = Field(
        gt=0,
        allow_inf_nan=False,
        description="Индексная цена в USD",
    )

    timestamp: int = Field(
        ge=0,
        description="UNIX timestamp в секундах",
    )
