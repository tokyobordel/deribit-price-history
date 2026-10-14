
from pydantic import BaseModel, ConfigDict, Field

from app.domain.tickers import Ticker


class CollectPriceTaskRequest(BaseModel):
    """Контракт входного сообщения задачи сбора цены."""

    model_config = ConfigDict(extra="forbid")

    ticker: Ticker = Field(
        description="Валютный индекс для получения цены",
    )
