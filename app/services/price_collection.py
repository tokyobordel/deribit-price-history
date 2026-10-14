
import time
from collections.abc import Callable

from app.domain.entities import Price
from app.domain.interfaces import PriceProviderInterface, PriceRepositoryInterface
from app.domain.tickers import Ticker
from app.services.interfaces import PriceCollectionServiceInterface


def current_unix_timestamp() -> int:
    return int(time.time())


class PriceCollectionService(PriceCollectionServiceInterface):
    """Сервис сбора индексных цен."""

    def __init__(
        self,
        provider: PriceProviderInterface,
        repository: PriceRepositoryInterface,
        clock: Callable[[], int] = current_unix_timestamp,
    ):
        self._provider = provider
        self._repository = repository
        self._clock = clock

    def collect(self, ticker: Ticker) -> Price:
        """Получить и сохранить текущую цену валюты."""

        # Получаем цену от внешнего провайдера
        value = self._provider.get_index_price(ticker)

        # Создаём доменную сущность
        price = Price(
            ticker=ticker,
            price=value,
            timestamp=self._clock(),
        )

        # Передаём сущность репозиторию
        self._repository.save(price)

        return price
