"""CLI entry point."""

from __future__ import annotations

import argparse
import json

from .rag import PermissionRAG


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Permission-aware RAG demo (secure vs vulnerable retrieval)."
    )
    parser.add_argument("question", help="User question")
    parser.add_argument(
        "--user",
        choices=["guest", "member", "admin"],
        default="guest",
        help="Simulated user role",
    )
    parser.add_argument(
        "--mode",
        choices=["secure", "vulnerable"],
        default="secure",
        help="secure = permission-filtered retrieval; vulnerable = no filter",
    )
    args = parser.parse_args()

    rag = PermissionRAG()
    response = rag.query(
        question=args.question,
        user_id=args.user,
        secure_mode=(args.mode == "secure"),
    )

    payload = {
        "query": response.query,
        "user_id": response.user_id,
        "secure_mode": response.secure_mode,
        "allowed_zones": sorted(response.allowed_zones),
        "retrieved": [
            {
                "zone": c.zone,
                "title": c.title,
                "score": round(c.score, 4),
            }
            for c in response.retrieved
        ],
        "leak_detected": response.leak_detected,
        "leak_reason": response.leak_reason,
        "answer": response.answer,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
