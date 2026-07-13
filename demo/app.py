"""Streamlit demo for permission-aware RAG."""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit runs this file from demo/; add project root so `import src` works.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.config import USER_LABELS, USER_LABELS_V2, USERS, USERS_V2
from src.rag import PermissionRAG, describe_user_access

st.set_page_config(
    page_title="Permission RAG Leakage Demo",
    page_icon="🔐",
    layout="wide",
)

st.title("Permission-Aware RAG Security Demo")
st.caption(
    "Phase 1: retrieval leakage (July 1). "
    "Phase 2: ACL RAG under cross-permission poisoning (July 13)."
)

experiment = st.radio(
    "Experiment",
    options=["leakage", "poisoning"],
    format_func=lambda x: "Phase 1 — Leakage (flat zones)" if x == "leakage" else "Phase 2 — Poisoning (groups/folders)",
    horizontal=True,
)

if experiment == "leakage":
    user_options = list(USERS.keys())
    user_labels = USER_LABELS
    corpus = "legacy"
    include_poison = True
    mode_options = ["secure", "vulnerable"]
else:
    user_options = list(USERS_V2.keys())
    user_labels = USER_LABELS_V2
    corpus = "v2"
    include_poison = st.checkbox("Include poisoned shared documents", value=True)
    mode_options = ["secure"]

cache_key = f"rag_{experiment}_{corpus}_{include_poison}"
if cache_key not in st.session_state:
    with st.spinner("Loading embedding model and documents (first run may take a minute)..."):
        st.session_state[cache_key] = PermissionRAG(
            corpus=corpus,
            include_poison=include_poison,
        )

col1, col2 = st.columns(2)
with col1:
    user_id = st.selectbox(
        "User role",
        options=user_options,
        format_func=lambda x: user_labels[x],
    )
with col2:
    mode = st.selectbox(
        "Retrieval mode",
        options=mode_options,
        help="Phase 2 always uses secure ACL (poisoning study with ACL enabled).",
    )

default_question = (
    "What is Project Alpha's total approved budget for 2025?"
    if experiment == "poisoning"
    else "What is Project Alpha's total approved budget for 2025?"
)
question = st.text_input("Question", value=default_question)

st.caption(describe_user_access(user_id))

if st.button("Ask", type="primary"):
    response = st.session_state[cache_key].query(
        question=question,
        user_id=user_id,
        secure_mode=(mode == "secure"),
    )

    if response.acl_violation:
        st.error("ACL VIOLATION: retrieved unauthorized folder(s).")
    elif response.leak_detected:
        st.error(f"LEAK DETECTED: {response.leak_reason}")
    elif response.poison_in_answer:
        st.error(f"POISON IN ANSWER: {response.poison_reason}")
    elif response.poison_retrieved:
        st.warning(f"POISON RETRIEVED (not yet in answer): {response.poison_reason}")
    else:
        st.success("No leak or poison detected for this user under current settings.")

    st.subheader("Answer")
    st.write(response.answer)

    st.subheader("Retrieved Documents")
    if not response.retrieved:
        st.info("No documents retrieved.")
    else:
        for chunk in response.retrieved:
            allowed = chunk.zone in response.allowed_zones
            badge = "allowed" if allowed else "UNAUTHORIZED"
            poison = " | POISONED" if chunk.is_poisoned else ""
            st.markdown(
                f"**[{chunk.zone}]** {chunk.title} — score={chunk.score:.3f} ({badge}{poison})"
            )
            st.code(chunk.text[:500] + ("..." if len(chunk.text) > 500 else ""))

with st.expander("Permission matrix"):
    if experiment == "leakage":
        st.markdown(
            """
| User | Allowed zones |
|------|----------------|
| guest | public |
| member | public, project_alpha |
| admin | public, project_alpha, confidential |
"""
        )
    else:
        st.markdown(
            """
| User | Groups | Readable folders | Writable folders |
|------|--------|------------------|------------------|
| intern | interns | public, shared | public, shared |
| researcher | engineering | public, shared, dept_internal | (none) |
| director | engineering, leadership | public, shared, dept_internal, executive | (none) |
"""
        )

st.markdown("---")
st.markdown(
    "**Suggested demo flow:** "
    "Phase 1: guest + vulnerable → leak; guest + secure → no leak. "
    "Phase 2: director + secure + poison on → poison in answer. "
    "Run batch eval: `python -m src.eval` and `python -m src.poison_eval`."
)
