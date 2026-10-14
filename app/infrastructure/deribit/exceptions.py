
class DeribitClientError(Exception):
    """Базовая ошибка интеграции с Deribit."""


class DeribitProtocolError(DeribitClientError):
    """Ответ не соответствует ожидаемому контракту."""


class DeribitAPIError(DeribitClientError):
    """Deribit вернул ошибку JSON-RPC."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

        super().__init__(
            f"Ошибка внешнего API[{code}]: {message}"
        )
