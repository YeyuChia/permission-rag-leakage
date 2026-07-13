"""Load synthetic enterprise documents grouped by permission zone or folder."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .config import (
    FOLDERS,
    POISON_MARKERS,
    ZONES,
    CorpusName,
    Document,
    corpus_dir,
)


def _poison_type_for_text(text: str, filename: str) -> str:
    upper_name = filename.upper()
    if "INSTRUCTION" in upper_name:
        return "instruction"
    if "POISONED" in upper_name:
        return "factual"
    lowered = text.lower()
    for poison_type, markers in POISON_MARKERS.items():
        if any(marker.lower() in lowered for marker in markers):
            return poison_type
    return ""


def load_documents(
    base_dir: Path | None = None,
    corpus: CorpusName = "legacy",
    include_poison: bool = True,
) -> List[Document]:
    root = base_dir or corpus_dir(corpus)
    zone_names = list(ZONES) if corpus == "legacy" else list(FOLDERS)
    documents: List[Document] = []

    for zone in zone_names:
        zone_dir = root / zone
        if not zone_dir.exists():
            continue

        for path in sorted(zone_dir.glob("*.txt")):
            if not include_poison and "POISONED" in path.name.upper():
                continue

            text = path.read_text(encoding="utf-8").strip()
            title = path.stem.replace("_", " ").title()
            doc_id = f"{zone}/{path.name}"
            poison_type = _poison_type_for_text(text, path.name)
            documents.append(
                Document(
                    doc_id=doc_id,
                    zone=zone,
                    title=title,
                    text=text,
                    source_path=str(path),
                    is_poisoned=bool(poison_type),
                    poison_type=poison_type,
                )
            )

    if not documents:
        raise FileNotFoundError(
            f"No documents found under {root} for corpus={corpus!r}"
        )

    return documents
