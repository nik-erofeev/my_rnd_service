import asyncio

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_core.messages import HumanMessage

from app.core.config import CONFIG
from app.services.RAG.llm.llm import AsyncLLM
from app.services.RAG.rag_pipeline.graph.builder import RAGGraphBuilder


langfuse = Langfuse(
    secret_key=CONFIG.langfuse.secret_key,
    public_key=CONFIG.langfuse.public_key,
    host=CONFIG.langfuse.base_url,
)


handler = CallbackHandler()


# example_ run
async def __main():
    _llm = AsyncLLM()
    graph_builder = RAGGraphBuilder(async_llm=_llm, use_answer_checker=True)
    graph = graph_builder.build()

    await graph.ainvoke(
        {"messages": [HumanMessage(content="ping langfuse")]},
        config={"callbacks": [handler]},
    )
    print("true")


if __name__ == "__main__":
    asyncio.run(__main())
