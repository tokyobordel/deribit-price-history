
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.infrastructure.persistence.price_repository import (
    SQLAlchemyPriceRepository,
)
from app.services.interfaces import PriceQueryServiceInterface
from app.services.price_query import PriceQueryService


def get_db_session() -> Iterator[Session]:
    """Предоставить сессию БД на время запроса."""

    session_factory = get_session_factory()

    with session_factory() as session:
        yield session


def get_price_query_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PriceQueryServiceInterface:
    """Создать сервис чтения цен."""

    repository = SQLAlchemyPriceRepository(session)

    return PriceQueryService(repository)
