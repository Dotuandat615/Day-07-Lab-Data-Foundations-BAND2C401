from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve.
        results = self.store.search(question, top_k=top_k)

        # 2. Build prompt — đánh số từng chunk để câu trả lời dễ "ground".
        if results:
            context = "\n\n".join(
                f"[{i}] {r['content']}" for i, r in enumerate(results, start=1)
            )
        else:
            context = "(no relevant context found)"

        prompt = (
            "You are a helpful assistant. Answer the question using ONLY the "
            "context below. If the context is insufficient, say so.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        # 3. Generate.
        return self.llm_fn(prompt)