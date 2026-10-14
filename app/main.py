
from fastapi import FastAPI

from app.api.prices import router as prices_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Deribit Price Service",
        description=(
            "API для получения исторических "
            "индексных цен BTC и ETH."
        ),
        version="0.1.0",
    )

    app.include_router(
        prices_router,
        prefix="/api",
    )

    return app


app = create_app()
