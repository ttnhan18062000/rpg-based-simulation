---
ticket_id: TCK-20260619-E63B-MANIFEST-MODEL
phase: investigation
date: 2026-06-23
---

# Investigation — TCK-20260619-E63B-MANIFEST-MODEL

## Key Findings

- `SimulationScenarioDefinition` uses `ConfigDict(frozen=True, extra="forbid")` — all new fields must be explicitly declared; uses Pydantic V2 with `from __future__ import annotations`
- Pydantic V2 with `from __future__ import annotations` makes ALL annotations strings; forward refs under `TYPE_CHECKING` won't resolve at model creation time → `RuntimeProfile` must be imported unconditionally
- `RuntimeProfile` made a Pydantic BaseModel (not a plain dataclass) so it integrates cleanly with `SimulationScenarioDefinition` validation
- Kahn's algorithm (BFS) for topological sort: deterministic within same level by sorting names lexicographically before enqueuing
