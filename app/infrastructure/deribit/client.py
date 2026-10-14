
import json
from decimal import Decimal

import httpx
from pydantic import ValidationError

from app.infrastructure.deribit.contracts import (
    GetIndexPriceRequest,
    GetIndexPriceResponse,
    DeribitErrorResponse,
)
from app.infrastructure.deribit.exceptions import (
    DeribitAPIError,
    DeribitProtocolError,
)
from app.domain.tickers import Ticker
from app.domain.interfaces import PriceProviderInterface


class DeribitClient(PriceProviderInterface):
    def __init__(self, http_client: httpx.Client):
        self._http_client = http_client

    def get_index_price(self, ticker: Ticker) -> Decimal:
        request = GetIndexPriceRequest(index_name=ticker)

        response = self._http_client.get(
            "public/get_index_price",
            params=request.model_dump(),
        )
        response.raise_for_status()

        try:
            payload = json.loads(
                response.text,
                parse_float=Decimal,
            )
        except json.JSONDecodeError as exc:
            raise DeribitProtocolError(
                "Внешнее API вернуло некорректный JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise DeribitProtocolError(
                "Ожидался JSON"
            )

        # JSON-RPC допускает result либо error
        has_result = "result" in payload
        has_error = "error" in payload

        if has_result == has_error:
            raise DeribitProtocolError(
                "Должен быть возвращен ровно один объект: результат или ошибка"
            )

        if has_error:
            try:
                error_response = (
                    DeribitErrorResponse.model_validate(payload)
                )
            except ValidationError as exc:
                raise DeribitProtocolError(
                    "Внешнее API вернуло некорректный JSON"
                ) from exc

            raise DeribitAPIError(
                code=error_response.error.code,
                message=error_response.error.message,
            )

        # Валидация успешного ответа
        try:
            result = GetIndexPriceResponse.model_validate(
                payload
            )
        except ValidationError as exc:
            raise DeribitProtocolError(
                "Invalid Deribit price response"
            ) from exc

        return result.result.index_price
