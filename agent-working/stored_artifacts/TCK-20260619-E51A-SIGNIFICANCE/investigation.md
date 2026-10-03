---
status: active
ticket_id: TCK-20260619-E51A-SIGNIFICANCE
artifact_type: investigation
date: 2026-06-21
---

# Investigation — TCK-20260619-E51A-SIGNIFICANCE

## Current Behavior

No `src/domains/chronicle/` directory exists. No significance scoring module exists anywhere in the codebase. The `NarrativeLedger` (E32D) is the upstream data source and is fully implemented.

**Key source files:**
- `src/domains/campaigns/state.py:L144` — `NarrativeLedgerEntry` frozen dataclass (episode, tick, event_type, subject_id, payload, significance, entry_id)
- `src/domains/campaigns/narrative_ledger.py:L23` — `NarrativeLedger` query facade
- `tests/unit/campaigns/test_narrative_ledger.py` — 35 passing tests (must remain green)

`NarrativeLedgerEntry.significance` is already a float field (0.0–1.0). The ticket's scorer re-derives significance from the `event_type` and `payload` fields — it does NOT read the `significance` field already on the entry (that field is set at ingestion time by the orchestrator). The scorer is an independent classification layer for the chronicle pipeline.

## Mechanics/Engine Constraints

- No Mechanics Bible chapter governs chronicle significance directly. `docs/mechanics/05_world_evolution.md` documents calamities and regional trauma as world-scale events — these map to `calamity` event type.
- Scoring must be deterministic: given the same `NarrativeLedgerEntry`, `score()` must always return the same float. No randomness.
- No durable state is created or mutated by this module — it is a pure stateless classifier.
- The module lives under `src/domains/chronicle/` (new domain package). No engine imports permitted.

## Parity Ledger Overlap

- `social_narrative.yaml` contains no chronicle-specific entries. A new entry `SOC-191` should be added after implementation to track the significance scoring formula.
- No existing parity entries are affected by this change (scorer is new, not a behavior change to existing code).

## Prior Work

- `stored_artifacts/TCK-20260619-E32D-NARRATIVE-LEDGER/investigation.md` — established `NarrativeLedgerEntry` schema and significance values (quest_completed=0.7, entity_death=0.5, faction_shift=0.9). The E51A ticket uses these same values as BASE_SIGNIFICANCE.
- `tickets/done/TCK-20260619-E51-CHRONICLE.md` — parent epic; defines child ticket structure and BASE_SIGNIFICANCE dict verbatim.
- No prior attempt at `EventSignificanceScorer` exists.

## Risks and Open Questions

1. **`__init__.py` for new package**: `src/domains/chronicle/` needs an `__init__.py` to be importable. Same for `tests/unit/chronicle/`.
2. **Test file location**: The ticket references `tests/unit/chronicle/test_chronicle_compiler.py`. This file does not exist; it must be created. The test functions named in the ACs must reside here.
3. **harvesting event type**: `test_significance_scoring_ranks_death_above_harvesting` requires a "harvesting" or equivalent event type. `BASE_SIGNIFICANCE` does not list "harvesting" — it will fall through to the default score of 0.1. This is correct behavior: default < entity_death (0.5).
4. **Determinism**: `score()` is a pure function of `entry.event_type` and `entry.payload.get("entity_role")`. No external state, no randomness. Determinism is guaranteed by design.

## Anti-Drift Hazards

- Do not import from `src/engine/` or `src/core/` — significance.py must remain dependency-free except for `NarrativeLedgerEntry`.
- Do not mutate `NarrativeLedgerEntry` — it is frozen.
- Do not add `significance` field recalculation to the NarrativeLedger itself — the scorer is a separate chronicle-layer concern.
