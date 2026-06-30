"""Load synthetic enterprise documents grouped by permission zone."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .config import Document, ZONES, data_dir


def load_documents(base_dir: Path | None = None) -> List[Document]:
    root = base_dir or data_dir()
    documents: List[Document] = []

    for zone in ZONES:
        zone_dir = root / zone
        if not zone_dir.exists():
            continue

        for path in sorted(zone_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            title = path.stem.replace("_", " ").title()
            doc_id = f"{zone}/{path.name}"
            documents.append(
                Document(
                    doc_id=doc_id,
                    zone=zone,
                    title=title,
                    text=text,
                    source_path=str(path),
                )
            )

    if not documents:
        raise FileNotFoundError(f"No documents found under {root}")

    return documents
