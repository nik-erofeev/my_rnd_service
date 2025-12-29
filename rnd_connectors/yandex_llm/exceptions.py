class BusinessException(Exception):
    """
    Базовый класс для бизнес-ошибок
    """

    pass


class YaGPTClientError(BusinessException, RuntimeError):
    """
    Ошибка клиента YaGPT client. бизнес-ошибка
    """

    pass
