"""Local embedding index using sentence-transformers."""

from __future__ import annotations

from typing import List, Literal, Tuple

import numpy as np

from .config import Document, RetrievedChunk

FilterMode = Literal["pre", "post"]


class EmbeddingIndex:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.documents: List[Document] = []
        self.embeddings: np.ndarray | None = None

    def build(self, documents: List[Document]) -> None:
        self.documents = documents
        texts = [f"{doc.title}\n{doc.text}" for doc in documents]
        self.embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def search(
        self,
        query: str,
        allowed_zones: set[str] | None,
        top_k: int = 3,
        filter_mode: FilterMode = "pre",
    ) -> List[RetrievedChunk]:
        if self.embeddings is None:
            raise RuntimeError("Index is empty. Call build() first.")

        query_vec = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        scores = self.embeddings @ query_vec
        ranked: List[Tuple[int, float]] = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True,
        )

        results: List[RetrievedChunk] = []
        for idx, score in ranked:
            doc = self.documents[idx]
            if filter_mode == "pre" and allowed_zones is not None:
                if doc.zone not in allowed_zones:
                    continue

            if filter_mode == "post" and allowed_zones is not None:
                if doc.zone not in allowed_zones:
                    continue

            results.append(
                RetrievedChunk(
                    doc_id=doc.doc_id,
                    zone=doc.zone,
                    title=doc.title,
                    text=doc.text,
                    score=float(score),
                    is_poisoned=doc.is_poisoned,
                    poison_type=doc.poison_type,
                )
            )
            if len(results) >= top_k:
                break

        return results
