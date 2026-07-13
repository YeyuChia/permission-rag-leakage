# Cross-Permission Security in Multi-User RAG Systems

A minimal reproduction project for **Project 1: Hierarchical RAG and Access Control**.

- **Phase 1 (July 1):** flat zones; shows cross-user **retrieval leakage** when ACL is missing.
- **Phase 2 (July 13):** users/groups/folders with overlapping permissions; studies **cross-permission poisoning** when ACL is enabled.

Related work: [AC-LORA (NeurIPS 2025)](https://proceedings.neurips.cc/paper_files/paper/2025/file/4e8b59ecd89b997ffbb8f2d146397f52-Paper-Conference.pdf), Permission Aware RAG, PoisonedRAG.

See [docs/threat_model.md](docs/threat_model.md) for the Phase 2 threat model.

## Quick Start

```bash
cd permission-rag-leakage
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 1) Single query (CLI)

```bash
# Secure mode: guest cannot see Project Alpha budget
python -m src "What is Project Alpha's total approved budget for 2025?" --user guest --mode secure

# Vulnerable mode: guest may retrieve confidential chunks
python -m src "What is Project Alpha's total approved budget for 2025?" --user guest --mode vulnerable
```

### 2) Phase 1 batch evaluation (leakage, 10 test cases)

```bash
python -m src.eval
```

Results: `results/leakage_results.csv`, `results/summary.json`

### 2b) Phase 2 poisoning evaluation (ACL always on)

```bash
python -m src.poison_eval
```

Results: `results/poison_results.csv`, `results/poison_summary.json`

Example Phase 2 query:

```bash
python -m src "What is Project Alpha's total approved budget for 2025?" --user director --corpus v2 --mode secure
```

### 3) Interactive demo (Streamlit)

```bash
streamlit run demo/app.py
```

## Optional: OpenAI answers

By default, the project uses **extractive answers** from retrieved chunks (no API key needed).

For fluent LLM answers, create `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Project Structure

```
permission-rag-leakage/
├── data/
│   ├── legacy/            # Phase 1 zones (public, project_alpha, confidential)
│   └── v2/                # Phase 2 folders (public, shared, dept_internal, executive)
├── src/                   # RAG + evaluation code
├── demo/app.py            # Streamlit UI
├── docs/                  # threat model, GitHub Pages
├── results/               # Generated after eval
└── requirements.txt
```

See [data/README.md](data/README.md) for corpus layout.

## Permission Models

### Phase 1 (legacy)

| User | Allowed zones |
|------|----------------|
| `guest` | public |
| `member` | public, project_alpha |
| `admin` | public, project_alpha, confidential |

### Phase 2 (Permission Aware RAG baseline)

| User | Groups | Readable folders | Writable folders |
|------|--------|------------------|------------------|
| `intern` | interns | public, shared | public, shared |
| `researcher` | engineering | public, shared, dept_internal | (none) |
| `director` | engineering, leadership | public, shared, dept_internal, executive | (none) |

`shared/` is the overlapping writable attack surface. Poisoned docs live there.

## Modes

- **secure**: retrieval only searches allowed zones/folders (ACL on)
- **vulnerable** (Phase 1 only): retrieval searches all zones

## Research direction

Not just "add ACL to RAG", but whether **ACL RAG stays secure under poisoning and overlapping permissions**.

## Future Work

- AI/ML paper corpus with folder-level ACL
- Post-filter vs pre-filter policy (Policy Aware Vector Search)
- Defense experiments (source trust, write-audit, chunk signing)
- LoRA memorization (AC-LORA)
