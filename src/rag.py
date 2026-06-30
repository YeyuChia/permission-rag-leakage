"""RAG pipeline with secure and vulnerable retrieval modes."""

from __future__ import annotations

import os
from typing import List, Set

from dotenv import load_dotenv

from .config import RAGResponse, SENSITIVE_MARKERS, USERS, RetrievedChunk
from .embed import EmbeddingIndex
from .load_data import load_documents

load_dotenv()


class PermissionRAG:
    def __init__(self, top_k: int = 3) -> None:
        self.top_k = top_k
        self.documents = load_documents()
        self.index = EmbeddingIndex()
        self.index.build(self.documents)

    def query(self, question: str, user_id: str, secure_mode: bool = True) -> RAGResponse:
        if user_id not in USERS:
            raise ValueError(f"Unknown user_id: {user_id}")

        allowed_zones: Set[str] = USERS[user_id]
        retrieval_filter = allowed_zones if secure_mode else None
        retrieved = self.index.search(
            query=question,
            allowed_zones=retrieval_filter,
            top_k=self.top_k,
        )

        answer = self._generate_answer(question, retrieved)
        leak_detected, leak_reason = detect_leak(user_id, retrieved, answer)

        return RAGResponse(
            query=question,
            user_id=user_id,
            secure_mode=secure_mode,
            allowed_zones=allowed_zones,
            retrieved=retrieved,
            answer=answer,
            leak_detected=leak_detected,
            leak_reason=leak_reason,
        )

    def _generate_answer(self, question: str, retrieved: List[RetrievedChunk]) -> str:
        if not retrieved:
            return (
                "I could not find relevant information in the documents you are allowed to access. "
                "You may need additional permissions."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return self._generate_with_openai(question, retrieved, api_key)

        return self._generate_extractive(question, retrieved)

    def _generate_extractive(
        self, question: str, retrieved: List[RetrievedChunk]
    ) -> str:
        """Fallback answer without external API: summarize retrieved chunks."""
        context_blocks = []
        for chunk in retrieved:
            context_blocks.append(f"[{chunk.zone}] {chunk.title}:\n{chunk.text}")

        context = "\n\n".join(context_blocks)
        return (
            f"Based on the retrieved internal documents, here is the answer to '{question}':\n\n"
            f"{context}\n\n"
            "(Extractive mode: set OPENAI_API_KEY for fluent LLM answers.)"
        )

    def _generate_with_openai(
        self, question: str, retrieved: List[RetrievedChunk], api_key: str
    ) -> str:
        from openai import OpenAI

        context = "\n\n".join(
            f"[zone={c.zone}] {c.title}\n{c.text}" for c in retrieved
        )
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        completion = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an enterprise knowledge assistant. "
                        "Answer ONLY using the provided context. "
                        "If the context is insufficient, say so."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
        )
        return completion.choices[0].message.content or ""


def detect_leak(
    user_id: str, retrieved: List[RetrievedChunk], answer: str
) -> tuple[bool, str]:
    allowed = USERS[user_id]

    leaked_zones = {chunk.zone for chunk in retrieved if chunk.zone not in allowed}
    if leaked_zones:
        return True, f"Retrieved unauthorized zone(s): {', '.join(sorted(leaked_zones))}"

    unauthorized_text = "\n".join(
        chunk.text for chunk in retrieved if chunk.zone not in allowed
    )
    for zone, markers in SENSITIVE_MARKERS.items():
        if zone in allowed:
            continue
        for marker in markers:
            if marker.lower() in unauthorized_text.lower():
                return True, f"Leaked content from '{zone}': {marker}"

    return False, ""
