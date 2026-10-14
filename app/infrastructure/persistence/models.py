
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Identity,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PriceModel(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric,
        nullable=False,
    )

    timestamp: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_prices_ticker_timestamp_id",
            "ticker",
            "timestamp",
            "id",
        ),
    )
