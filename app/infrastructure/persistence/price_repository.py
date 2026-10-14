
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import Price
from app.domain.tickers import Ticker
from app.infrastructure.persistence.models import PriceModel
from app.domain.interfaces import PriceRepositoryInterface


class SQLAlchemyPriceRepository(PriceRepositoryInterface):
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: PriceModel) -> Price:
        return Price(
            ticker=Ticker(model.ticker),
            price=model.price,
            timestamp=model.timestamp,
        )

    def save(self, price: Price) -> None:
        model = PriceModel(
            ticker=price.ticker.value,
            price=price.price,
            timestamp=price.timestamp,
        )

        self._session.add(model)
        self._session.flush()

    def get_all(self, ticker: Ticker) -> list[Price]:
        stmt = (
            select(PriceModel)
            .where(PriceModel.ticker == ticker.value)
            .order_by(
                PriceModel.timestamp.asc(),
                PriceModel.id.asc(),
            )
        )

        models = self._session.scalars(stmt).all()

        return [self._to_domain(model) for model in models]

    def get_latest(self, ticker: Ticker) -> Price | None:
        stmt = (
            select(PriceModel)
            .where(PriceModel.ticker == ticker.value)
            .order_by(
                PriceModel.timestamp.desc(),
                PriceModel.id.desc(),
            )
            .limit(1)
        )

        model: PriceModel | None = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_domain(model)

    def get_by_period(
        self,
        ticker: Ticker,
        start_timestamp: int,
        end_timestamp: int,
    ) -> list[Price]:
        if start_timestamp > end_timestamp:
            raise ValueError(
                "start_timestamp must not exceed end_timestamp"
            )

        stmt = (
            select(PriceModel)
            .where(
                PriceModel.ticker == ticker.value,
                PriceModel.timestamp >= start_timestamp,
                PriceModel.timestamp < end_timestamp,
            )
            .order_by(
                PriceModel.timestamp.asc(),
                PriceModel.id.asc(),
            )
        )

        models = self._session.scalars(stmt).all()

        return [self._to_domain(model) for model in models]
