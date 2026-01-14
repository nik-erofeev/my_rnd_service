class TYKClientError(Exception):
    """Ошибка взаимодействия с TYK Gateway"""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)
