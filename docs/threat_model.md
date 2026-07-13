# Threat Model: Cross-Permission Poisoning in ACL RAG

## Research question

In a permission-aware RAG system with overlapping access, can poisoned lower-privilege
or shared documents influence higher-privilege users' outputs **even when ACL filtering
is enabled at retrieval time**?

## Setup (Permission Aware RAG baseline)

- **Users** map to **groups**, groups map to **folders**.
- **Overlapping permissions**: `director` belongs to `engineering` and `leadership`.
- **Shared folder**: readable by all groups; writable by `intern` only.
- **Retrieval policy**: pre-filter (only embed/search documents in allowed folders).

Inspired by Permission Aware RAG (IAM-style access resolution) and enterprise systems
such as [Azure AI Search document-level access](https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview)
and [Amazon Kendra user context filtering](https://docs.aws.amazon.com/kendra/latest/dg/user-context-filter.html).

## Attacker / victim

| Role | Capability |
|------|------------|
| **Attacker (`intern`)** | Can write `public` and `shared` documents |
| **Victim (`director`)** | Can read `shared`, `dept_internal`, `executive` (ACL on) |

## Attack (PoisonedRAG-style)

1. Attacker injects poisoned chunks into `shared/` (factual false budget or instruction injection).
2. Victim asks a legitimate question (e.g., Project Alpha budget).
3. ACL allows retrieval from `shared` (authorized overlap).
4. Poisoned chunk enters top-k context and may appear in the answer.

This is **not** an ACL bypass. It is an **authorized-but-poisoned** retrieval risk.

## Metrics

| Metric | Meaning |
|--------|---------|
| **RSR** (Retrieval Success Rate) | Poison chunk appears in top-k |
| **ASR** (Attack Success Rate) | Answer contains poison markers / false value |
| **ACL violation** | Retrieved folder outside user's allowed set (should be 0 in secure mode) |

## What this does NOT cover yet

- Post-filter vector search policies (Policy Aware Vector Search)
- LoRA memorization (AC-LORA)
- Real AI/ML paper corpus (planned next step)

## Run experiments

```bash
python -m src.poison_eval
```

Example single query:

```bash
python -m src "What is Project Alpha's total approved budget for 2025?" --user director --corpus v2 --mode secure
```
