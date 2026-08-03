from __future__ import annotations

import os
from typing import Callable

from .store import EmbeddingStore

from openai import OpenAI


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        self.store = store

        if llm_fn is not None:
            self.llm_fn = llm_fn
        else:
            # Khởi tạo mặc định với OpenAI API
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                def default_openai_llm(prompt: str) -> str:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                    )
                    return response.choices[0].message.content or ""

                self.llm_fn = default_openai_llm
            except Exception as e:
                # Fallback nếu không có thư viện openai hoặc thiếu API Key
                def fallback_llm(prompt: str) -> str:
                    return f"[OpenAI Client Error: {e}] Answer based on context."

                self.llm_fn = fallback_llm
        pass

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        results = self.store.search(query=question, top_k=top_k)

        context_chunks = [res.get("content", "") for res in results if res.get("content")]
        context_str = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."

        prompt = (
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            f"Answer the question based strictly on the context provided above."
        )

        return self.llm_fn(prompt)
        raise NotImplementedError("Implement KnowledgeBaseAgent.answer")
