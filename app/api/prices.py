
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.api.dependencies import get_price_query_service
from app.api.schemas import (
    PriceResponse,
    PricesByDateQueryParams,
    TickerQueryParams,
)
from app.domain.entities import Price
from app.services.interfaces import PriceQueryServiceInterface


router = APIRouter(
    prefix="/prices",
    tags=["Prices"],
)


@router.get(
    "",
    response_model=list[PriceResponse],
    summary="Получить историю цен",
    description="Все сохранённые цены указанной валюты.",
)
def get_all_prices(
    params: Annotated[TickerQueryParams, Query()],
    service: Annotated[
        PriceQueryServiceInterface,
        Depends(get_price_query_service),
    ],
) -> list[Price]:
    return service.get_all(params.ticker)


@router.get(
    "/latest",
    response_model=PriceResponse,
    summary="Получить последнюю цену",
    description="Последняя сохранённая цена валюты.",
    responses={
        404: {
            "description": "Для валюты нет сохранённых цен",
        },
    },
)
def get_latest_price(
    params: Annotated[TickerQueryParams, Query()],
    service: Annotated[
        PriceQueryServiceInterface,
        Depends(get_price_query_service),
    ],
) -> Price:
    price = service.get_latest(params.ticker)

    if price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No saved prices for ticker "
                f"'{params.ticker.value}'"
            ),
        )

    return price


@router.get(
    "/by-date",
    response_model=list[PriceResponse],
    summary="Получить цены за дату",
    description="Все цены за календарный день по UTC.",
)
def get_prices_by_date(
    params: Annotated[PricesByDateQueryParams, Query()],
    service: Annotated[
        PriceQueryServiceInterface,
        Depends(get_price_query_service),
    ],
) -> list[Price]:
    return service.get_by_date(
        ticker=params.ticker,
        target_date=params.date,
    )
