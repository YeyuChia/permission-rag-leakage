# Cross-Permission Information Leakage in Multi-User RAG Systems

A minimal reproduction project for **Project 1: Hierarchical RAG and Access Control**.

This demo simulates an enterprise RAG chatbot with three permission zones and three user roles. It shows how **missing retrieval-time permission filtering** can cause cross-user information leakage.

Related work: [AC-LORA (NeurIPS 2025)](https://proceedings.neurips.cc/paper_files/paper/2025/file/4e8b59ecd89b997ffbb8f2d146397f52-Paper-Conference.pdf)

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

### 2) Batch evaluation (10 test cases)

```bash
python -m src.eval
```

Results are saved to:
- `results/leakage_results.csv`
- `results/summary.json`

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
├── data/                  # Synthetic docs by permission zone
├── src/                   # RAG + evaluation code
├── demo/app.py            # Streamlit UI
├── docs/index.html        # GitHub Pages landing page
├── results/               # Generated after eval
└── requirements.txt
```

## Permission Model

| Zone | Content |
|------|---------|
| `public` | Company overview |
| `project_alpha` | Project budget & roadmap |
| `confidential` | HR layoff plan & executive salary |

| User | Allowed zones |
|------|----------------|
| `guest` | public |
| `member` | public, project_alpha |
| `admin` | all zones |

## Secure vs Vulnerable

- **secure**: retrieval only searches documents in the user's allowed zones
- **vulnerable**: retrieval searches **all** zones (simulates missing access control filter)

## GitHub Pages

Enable Pages in repo settings:
- Source: `Deploy from a branch`
- Branch: `main` / folder: `/docs`

## Deliverables Checklist (July 1)

- [x] GitHub repository
- [ ] GitHub Pages enabled
- [ ] Video demo recorded
- [ ] 10-page slide deck

## Future Work

- LoRA-based isolation (AC-LORA-style adapter routing)
- Output-side audit/filtering
- Hierarchical RBAC inheritance
- Memorization leakage beyond retrieval errors
