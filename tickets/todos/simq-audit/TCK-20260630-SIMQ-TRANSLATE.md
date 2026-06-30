---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-TRANSLATE
phase: open
date: 2026-06-30
tags: [simulation-quality, observability, event-translation, audit]
---

# TCK-20260630-SIMQ-TRANSLATE

## Title
Translation table completeness audit and event type coverage doc

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Audit every `event_type` emitted by the engine (via `event_extractor.py` and the event bus)
against the `SCORER_REGISTRY` in `QualityHub`. Produce a coverage document that classifies
every emitted event type as: (a) scored by SimQ, (b) P0-A blocked (never emitted yet),
(c) translation gap (emitted but not reaching the right scorer), or (d) intentionally unscored.

## Scope
1. Extract all `event_type` values emitted in `simulation_events.jsonl` from a long
   calibration run (1000-tick sandbox_world after TCK-20260630-SIMQ-CALFIX)
2. Extract all `event_type` values registered in `SCORER_REGISTRY` (from scorer EVENT_TYPES)
3. Extract all `event_type` → `contract_type` mappings from `_TRANSLATE_SIMPLE` and
   `_TRANSLATE_CONDITIONAL` in `quality_hub.py`
4. For each emitted type: classify against the registry
5. For each registry type with zero calibration hits: confirm P0-A blocked or find gap
6. Write `docs/simulation_quality/event_type_coverage.md` with the full classification table
7. If any translation gaps are found: fix them in the same ticket (scope is small)

## Out of Scope
- Adding new scoring rules (only translation/routing fixes, not new scorer logic)
- Fixing P0-A blocked events (they're not emitted, nothing to translate)

## Acceptance Criteria
- [ ] `docs/simulation_quality/event_type_coverage.md` committed with full classification table
- [ ] Every emitted event_type accounted for (scored / blocked / unscored with reason)
- [ ] Every scorer EVENT_TYPE with zero calibration hits marked as P0-A blocked or gap
- [ ] Any translation gaps found: fixed in `quality_hub.py` with a test
- [ ] `make knowledge-index-update` run after doc committed

## Related Tickets
- TCK-20260630-SIMQ-CALFIX (prerequisite — need world-loaded calibration runs)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track D
- `docs/simulation_quality/quality_scoring_contract.md` §8.1 (event routing)

## Related Code Areas
- `src/simulation_quality/quality_hub.py` — `_TRANSLATE_SIMPLE`, `_TRANSLATE_CONDITIONAL`, `SCORER_REGISTRY`
- `src/observability/event_extractor.py` — all `event_type=` literals (source of truth)
- `src/simulation_quality/scorers/*.py` — `EVENT_TYPES` tuples

## Assumptions / Open Questions
- Some event types are emitted conditionally (e.g., `boss_spawned` requires world_boss kind).
  These should be classified as "world-infrastructure-gated" (subset of P0-A blocked).
- The `InvariantViolation` engine event → `combat_hard_law_violation` / `conservation_law_violated`
  conditional translation should be verified against real hard law events.

## Implementation Notes
- Script to extract emitted event types from JSONL:
  ```python
  import json, collections
  counts = collections.Counter()
  with open("data/runs/.../simulation_events.jsonl") as f:
      for line in f:
          d = json.loads(line)
          counts[d.get("event_type", "?")] += 1
  ```
- Cross-reference against `SCORER_REGISTRY.keys()` and translation table keys.

## Test Summary
- If translation gaps are fixed: add tests to `test_quality_hub_event_translation.py`
- Coverage doc is the primary deliverable; no behavioral test changes unless gaps are fixed

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
