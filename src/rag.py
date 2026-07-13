"""RAG pipeline with secure and vulnerable retrieval modes."""

from __future__ import annotations

import os
from typing import List, Set

from dotenv import load_dotenv

from .access import resolve_access
from .config import (
    POISON_MARKERS_FLAT,
    RAGResponse,
    SENSITIVE_MARKERS,
    USERS,
    USERS_V2,
    CorpusName,
    RetrievedChunk,
    allowed_zones_for_user,
    is_v2_user,
)
from .embed import EmbeddingIndex, FilterMode
from .load_data import load_documents

load_dotenv()


class PermissionRAG:
    def __init__(
        self,
        top_k: int = 3,
        corpus: CorpusName = "legacy",
        include_poison: bool = True,
        filter_mode: FilterMode = "pre",
    ) -> None:
        self.top_k = top_k
        self.corpus = corpus
        self.include_poison = include_poison
        self.filter_mode = filter_mode
        self.documents = load_documents(
            corpus=corpus,
            include_poison=include_poison,
        )
        self.index = EmbeddingIndex()
        self.index.build(self.documents)

    def query(self, question: str, user_id: str, secure_mode: bool = True) -> RAGResponse:
        if user_id not in USERS and user_id not in USERS_V2:
            raise ValueError(f"Unknown user_id: {user_id}")

        allowed_zones: Set[str] = allowed_zones_for_user(user_id)
        retrieval_filter = allowed_zones if secure_mode else None
        retrieved = self.index.search(
            query=question,
            allowed_zones=retrieval_filter,
            top_k=self.top_k,
            filter_mode=self.filter_mode,
        )

        answer = self._generate_answer(question, retrieved)
        leak_detected, leak_reason = detect_leak(user_id, retrieved, answer)
        poison_retrieved, poison_in_answer, poison_reason = detect_poison(
            retrieved, answer
        )
        acl_violation = bool(
            secure_mode
            and any(chunk.zone not in allowed_zones for chunk in retrieved)
        )

        return RAGResponse(
            query=question,
            user_id=user_id,
            secure_mode=secure_mode,
            allowed_zones=allowed_zones,
            retrieved=retrieved,
            answer=answer,
            leak_detected=leak_detected,
            leak_reason=leak_reason,
            poison_retrieved=poison_retrieved,
            poison_in_answer=poison_in_answer,
            poison_reason=poison_reason,
            acl_violation=acl_violation,
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
    allowed = allowed_zones_for_user(user_id)

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


def detect_poison(
    retrieved: List[RetrievedChunk], answer: str
) -> tuple[bool, bool, str]:
    poison_chunks = [chunk for chunk in retrieved if chunk.is_poisoned]
    if poison_chunks:
        titles = ", ".join(chunk.title for chunk in poison_chunks)
        retrieved_hit = True
        retrieved_reason = f"Retrieved poisoned chunk(s): {titles}"
    else:
        retrieved_hit = False
        retrieved_reason = ""

    answer_hit = any(marker.lower() in answer.lower() for marker in POISON_MARKERS_FLAT)
    if answer_hit:
        answer_reason = "Answer contains poison marker text"
    else:
        answer_reason = ""

    if retrieved_hit and answer_hit:
        return True, True, f"{retrieved_reason}; {answer_reason}"
    if retrieved_hit:
        return True, False, retrieved_reason
    if answer_hit:
        return False, True, answer_reason
    return False, False, ""


def describe_user_access(user_id: str) -> str:
    if is_v2_user(user_id):
        ctx = resolve_access(user_id)
        groups = ", ".join(sorted(ctx.groups))
        readable = ", ".join(sorted(ctx.readable_folders))
        writable = ", ".join(sorted(ctx.writable_folders)) or "(none)"
        return (
            f"groups=[{groups}], readable=[{readable}], writable=[{writable}]"
        )
    return f"zones={sorted(allowed_zones_for_user(user_id))}"
