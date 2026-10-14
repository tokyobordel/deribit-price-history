
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.tickers import Ticker


class GetIndexPriceRequest(BaseModel):
    """Параметры GET /public/get_index_price."""

    index_name: Ticker


class GetIndexPriceResult(BaseModel):
    """Данные успешного ответа Deribit."""

    index_price: Decimal = Field(
        gt=0,
        allow_inf_nan=False,
    )
    estimated_delivery_price: Decimal


class DeribitResponseEnvelope(BaseModel):
    """Общие поля ответа Deribit JSON-RPC 2.0."""

    model_config = ConfigDict(extra="ignore")

    jsonrpc: Literal["2.0"]
    id: int | str | None = None

    testnet: bool | None = None

    us_in: int | None = Field(default=None, alias="usIn")
    us_out: int | None = Field(default=None, alias="usOut")
    us_diff: int | None = Field(default=None, alias="usDiff")


class GetIndexPriceResponse(DeribitResponseEnvelope):
    """Успешный ответ GET /public/get_index_price."""

    result: GetIndexPriceResult


class DeribitError(BaseModel):
    """Описание ошибки JSON-RPC."""

    code: int
    message: str
    data: Any = None


class DeribitErrorResponse(DeribitResponseEnvelope):
    """Ответ Deribit с ошибкой."""

    error: DeribitError
