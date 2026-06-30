"""Streamlit demo for permission-aware RAG."""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit runs this file from demo/; add project root so `import src` works.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.config import USER_LABELS, USERS
from src.rag import PermissionRAG

st.set_page_config(
    page_title="Permission RAG Leakage Demo",
    page_icon="🔐",
    layout="wide",
)

st.title("Permission-Aware RAG Leakage Demo")
st.caption(
    "Reproduction study inspired by access control challenges in enterprise RAG systems "
    "(related: AC-LORA, NeurIPS 2025)."
)

if "rag" not in st.session_state:
    with st.spinner("Loading embedding model and documents (first run may take a minute)..."):
        st.session_state.rag = PermissionRAG()

col1, col2 = st.columns(2)
with col1:
    user_id = st.selectbox(
        "User role",
        options=list(USERS.keys()),
        format_func=lambda x: USER_LABELS[x],
    )
with col2:
    mode = st.selectbox(
        "Retrieval mode",
        options=["secure", "vulnerable"],
        help="secure = filter by permission; vulnerable = search all zones (buggy system)",
    )

question = st.text_input(
    "Question",
    value="What is Project Alpha's total approved budget for 2025?",
)

if st.button("Ask", type="primary"):
    response = st.session_state.rag.query(
        question=question,
        user_id=user_id,
        secure_mode=(mode == "secure"),
    )

    if response.leak_detected:
        st.error(f"LEAK DETECTED: {response.leak_reason}")
    else:
        st.success("No leak detected for this user under current settings.")

    st.subheader("Answer")
    st.write(response.answer)

    st.subheader("Retrieved Documents")
    if not response.retrieved:
        st.info("No documents retrieved.")
    else:
        for chunk in response.retrieved:
            allowed = chunk.zone in response.allowed_zones
            badge = "allowed" if allowed else "UNAUTHORIZED"
            st.markdown(f"**[{chunk.zone}]** {chunk.title} — score={chunk.score:.3f} ({badge})")
            st.code(chunk.text[:500] + ("..." if len(chunk.text) > 500 else ""))

with st.expander("Permission matrix"):
    st.markdown(
        """
| User | Allowed zones |
|------|----------------|
| guest | public |
| member | public, project_alpha |
| admin | public, project_alpha, confidential |
"""
    )

st.markdown("---")
st.markdown(
    "**Suggested demo flow for video:** "
    "1) guest + secure → no leak; "
    "2) guest + vulnerable → budget leak; "
    "3) show evaluation via `python -m src.eval`."
)
