class RagPipelineError(Exception):
    """
    Ошибка в пайплайне. Бизнес-ошибка
    """

    def __init__(self, message: str = ""):
        self.message = message
