---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-EVALUATION
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261004-IMPORT-LINTER-EVALUATION

- Audit (1c443a957): grimp over `src` as is sees 215 of 744 modules because `core`, `api`, `perf`, `certification`, `content_semantics` have no `__init__.py`; imports mix `src.x` (2,764) and bare `x`.
- Registry (859eec3d5): `layer` field with six layers; the `layers` contract reads it.
- `uvx --from grimp` works under the memory cap (1.7 s for a trivial run). The brief's inventory is an unverified read-only search.
- Measured (see the record): 20 of 36 packages namespace; `src` + `src.<pkg>` x20 gives full coverage except `src/engine/intent`; `random` cannot be a root package; `exclude_type_checking_imports` is root-level; unmatched `ignore_imports` is an error by default (found one stale allowlist entry).
- Inventory by subagent: 50 rules in 29 files (summary said 53); not verified rule by rule.
