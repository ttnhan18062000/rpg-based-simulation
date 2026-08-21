---
status: active
layer: engine
authority: P1
audience: developer
---

# Phase 13 Retirement Manifest

## Purpose

Records the authoritative retirement plan for legacy systems and compatibility
shims that are no longer required after Phase 12 stabilisation. Any code or
data path listed here must be removed before Phase 13 is declared complete.

## Core Logic & Engine

| Component | Retirement Condition | Target Phase |
|---|---|---|
| Legacy fallback maps (`_FALLBACK_*` dicts) | All IDs covered by `migration_map.yaml` | Phase 13 |
| `LEGACY_FALLBACK` RuntimeContentMode | No callers remain outside test helpers | Phase 13 |
| V1 entity builder shims | All construction paths use `V2EntityBuilder` | Phase 13 |
| Legacy parity oracle stubs | Replaced by live parity harness results | Phase 13 |

## Retirement Protocol

1. Verify zero test failures with the component removed (run `pytest -m "not slow"`).
2. Update `docs/guidelines/intentional_divergences.md` to close the divergence entry.
3. Remove the `KNOWN_HARDCODED_BASELINE` entry (if applicable).
4. Update `data/content/compatibility/migration_map.yaml` to mark the ID `retired`.
5. Add a `tickets/done/` entry referencing the removal commit.
