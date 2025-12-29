from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


# class RAGState(TypedDict):
class RAGState(TypedDict, total=False):
    """Состояние, передаваемое между узлами графа обработки RAG.

    Содержит сообщения пользователя, найденные документы и информацию о намерениях.

    Attributes:
        messages (list[BaseMessage]): История сообщений (дополняется на каждом шаге).
        retrieved (list[Any]): Список найденных документов (результат работы ретривера).
        intent (list[BaseMessage]): Классифицированные намерения пользователя.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    retrieved: list[Any]
    intent: Annotated[list[BaseMessage], add_messages]
