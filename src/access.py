"""IAM-style access resolution for Permission Aware RAG (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Set

from .config import (
    FOLDER_SENSITIVITY,
    USERS_V2,
    WRITABLE_FOLDERS,
    allowed_folders,
)


@dataclass(frozen=True)
class AccessContext:
    user_id: str
    groups: Set[str]
    readable_folders: Set[str]
    writable_folders: Set[str]

    def folder_sensitivity(self, folder: str) -> str:
        return FOLDER_SENSITIVITY.get(folder, "unknown")


def resolve_access(user_id: str) -> AccessContext:
    """User identity -> group membership -> folder-level read/write sets."""
    if user_id not in USERS_V2:
        raise ValueError(f"Not a Phase-2 user: {user_id}")

    return AccessContext(
        user_id=user_id,
        groups=set(USERS_V2[user_id]),
        readable_folders=allowed_folders(user_id),
        writable_folders=set(WRITABLE_FOLDERS.get(user_id, set())),
    )
