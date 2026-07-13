"""CLI entry point."""

from __future__ import annotations

import argparse
import json

from .config import USERS, USERS_V2
from .rag import PermissionRAG, describe_user_access


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Permission-aware RAG demo (leakage + poisoning experiments)."
    )
    parser.add_argument("question", help="User question")
    parser.add_argument(
        "--user",
        default="guest",
        help="Simulated user role (legacy: guest/member/admin; v2: intern/researcher/director)",
    )
    parser.add_argument(
        "--mode",
        choices=["secure", "vulnerable"],
        default="secure",
        help="secure = permission-filtered retrieval; vulnerable = no filter",
    )
    parser.add_argument(
        "--corpus",
        choices=["legacy", "v2"],
        default="legacy",
        help="legacy = data/legacy flat zones; v2 = data/v2 groups/folders poisoning setup",
    )
    parser.add_argument(
        "--include-poison",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include poisoned shared documents when corpus=v2",
    )
    args = parser.parse_args()

    valid_users = set(USERS) | set(USERS_V2)
    if args.user not in valid_users:
        parser.error(f"Unknown user {args.user!r}. Valid: {sorted(valid_users)}")

    rag = PermissionRAG(
        corpus=args.corpus,
        include_poison=args.include_poison,
    )
    response = rag.query(
        question=args.question,
        user_id=args.user,
        secure_mode=(args.mode == "secure"),
    )

    payload = {
        "query": response.query,
        "user_id": response.user_id,
        "access": describe_user_access(response.user_id),
        "corpus": args.corpus,
        "secure_mode": response.secure_mode,
        "allowed_zones": sorted(response.allowed_zones),
        "retrieved": [
            {
                "zone": c.zone,
                "title": c.title,
                "score": round(c.score, 4),
                "is_poisoned": c.is_poisoned,
                "poison_type": c.poison_type,
            }
            for c in response.retrieved
        ],
        "leak_detected": response.leak_detected,
        "leak_reason": response.leak_reason,
        "poison_retrieved": response.poison_retrieved,
        "poison_in_answer": response.poison_in_answer,
        "poison_reason": response.poison_reason,
        "acl_violation": response.acl_violation,
        "answer": response.answer,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
