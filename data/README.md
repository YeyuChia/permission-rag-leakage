# Data layout

Two corpora live under separate directories. Only one is loaded per run (`--corpus legacy` or `--corpus v2`).

```
data/
├── legacy/          # Phase 1 — flat zones, leakage demo
│   ├── public/
│   ├── project_alpha/
│   └── confidential/
└── v2/              # Phase 2 — groups/folders, Permission-Aware baseline + poisoning
    ├── public/
    ├── shared/
    ├── dept_internal/
    └── executive/
```

| Corpus | CLI | Users | Folders loaded |
|--------|-----|-------|----------------|
| `legacy` | `--corpus legacy` (default) | guest, member, admin | `data/legacy/{public,project_alpha,confidential}` |
| `v2` | `--corpus v2` | intern, researcher, director | `data/v2/{public,shared,dept_internal,executive}` |

Poisoned documents (Phase 2 only): `data/v2/shared/*POISONED*`. Omit with `include_poison=False` for a clean baseline.
