from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import EmbeddingConfig


class Embedding:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.model_kwargs = {"device": config.device}
        self.embeddings = HuggingFaceEmbeddings(
            **{"model_name": self.config.model, "model_kwargs": self.model_kwargs},
        )

    def get_embeddings_model(self) -> HuggingFaceEmbeddings:
        return self.embeddings
