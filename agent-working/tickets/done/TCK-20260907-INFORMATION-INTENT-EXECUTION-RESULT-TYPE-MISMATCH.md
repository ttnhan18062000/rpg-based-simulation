---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-MISMATCH
phase: done
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-MISMATCH

## Title
InformationIntentExecutionPhase never strips the raw ActionIntent it executes from intent_results, crashing StrategicWorkQueue.build()

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while implementing `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`
(Dormant Mechanism Closure epic): once that ticket's own persistence fix finally let
`InformationBeliefPhase.apply()` Branch 3 (`src/domains/information/phase.py:86-104`) fire for
the first time in any real run, exercising it with `ENABLE_INFORMATION_INTENT_EXECUTION=ON`
crashed:

```
AttributeError: 'ActionIntent' object has no attribute 'accepted'
  at src/systems/strategic_systems/work_queue.py:55, StrategicWorkQueue.build()
```

**Root cause**: Branch 3 stores a raw, unresolved `ActionIntent` object directly into
`EntityUpdate.intent_results` — a field typed `List[IntentResult]` (`src/core/state.py:821`, "the
outcome of a specific resource transfer intent," with a real `.accepted` field `ActionIntent` does
not have). `InformationIntentExecutionPhase.execute()`
(`src/engine/pipeline_phases/information_intent_execution.py`) is the dedicated production call
site meant to resolve it via `ActionIntentAdapter.execute()`, and correctly filters for
`isinstance(candidate, ActionIntent)` before executing — but never removed or replaced the raw
`ActionIntent` entry afterward. `EntityUpdate.merge()` (`src/core/updates.py:779`) concatenates
`intent_results` additively, so the raw, still-unresolved candidate survived unchanged and got
installed as `entity.identity.latest_intent_results`
(`src/engine/patches.py:236`), where `StrategicWorkQueue.build()` reads `.accepted` off every
entry unconditionally and crashes.

This is dormant, pre-existing code — `InformationIntentExecutionPhase` itself had never been
exercised by any real corpus world before, since Branch 3 could never previously fire (see the
sibling ticket above) to feed it a real `ActionIntent`.

For comparison, the one other real call site of `ActionIntentAdapter.execute()`
(`src/engine/tactical.py:333-350`) resolves an `ActionIntent` synchronously in the same phase and
never round-trips it through `intent_results` at all — confirming `intent_results` was never meant
to carry an unresolved `ActionIntent`, only real `IntentResult` outcomes.

## Scope
- Fix `InformationIntentExecutionPhase.execute()` to strip the raw `ActionIntent` entries from an
  entity's own `intent_results` once they've been passed to `ActionIntentAdapter.execute()`, so
  they never survive into `entity.identity.latest_intent_results`.
- Preserve any real `IntentResult` entries that may coexist in the same list (mixed-list case,
  already covered by an existing test).
- Prove the fix by re-running `unit_information_routing_pilot`'s calibration with
  `ENABLE_INFORMATION_INTENT_EXECUTION=ON` — must no longer crash, and `route_new_query` must
  actually fire.
- Re-verify no regression on the 3 real worlds already shipping `information_source_profiles`
  (`urban_political`, `unit_information_source`, `unit_information_density`).

## Out of Scope
- Redesigning `InformationQueryRouter`/`InformationIntentResolver`'s own matching logic — confirmed
  correct.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [x] `InformationIntentExecutionPhase.execute()` never lets a raw `ActionIntent` survive into its
      returned update's `intent_results`.
- [x] `unit_information_routing_pilot` calibration (`ENABLE_INFORMATION_INTENT_EXECUTION=ON`) no
      longer crashes; `route_new_query` fires (INFORMATION pillar moves off `grade=C events=0`).
- [x] No regression on the 3 real worlds already shipping `information_source_profiles`.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` (`tickets/done/` — the ticket
  this hotfix unblocks; found while implementing it)
- `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` (`tickets/done/` — built
  `unit_information_routing_pilot`, the corpus world that first exercised this bug)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-270`, `ENABLE_INFORMATION_INTENT_EXECUTION`)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/engine/pipeline_phases/information_intent_execution.py`
- `src/domains/information/phase.py`
- `src/systems/strategic_systems/work_queue.py`
- `src/core/updates.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Fix (`src/engine/pipeline_phases/information_intent_execution.py`,
`InformationIntentExecutionPhase.execute()`): for each entity with at least one raw `ActionIntent`
candidate in `intent_results`, replace that entity's own `refined_entity_updates[eid]` with its
`intent_results` filtered to drop every `ActionIntent` instance — done BEFORE executing the
candidates and merging in `adapter_updates`, so the later additive `EntityUpdate.merge()` starts
from the cleaned list, not the raw one. Real `IntentResult` entries in the same list (the
already-tested mixed-list case) are preserved untouched.

## Test Summary
Added 2 new tests to `tests/unit/engine/test_information_intent_execution_phase.py`:
`test_action_intent_execution_phase_strips_raw_action_intent_after_execution` (proves the raw
`ActionIntent` no longer survives) and
`test_action_intent_execution_phase_preserves_real_intent_result_alongside_stripped_action_intent`
(proves the mixed-list case still preserves the real `IntentResult`). All 5 tests in that file
pass. `pytest tests/unit/engine/ tests/unit/domains/information/
tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q -m "not slow"` → 234
passed, 1 skipped, 3 deselected.

Real calibration proof: `ENABLE_INFORMATION_INTENT_EXECUTION=ON python3 tools/calibrate_simq.py
--name unit_information_routing_pilot --seed 42 --ticks 200` → no crash, `overall_grade=A`,
INFORMATION `grade=B events=1`. Confirmed via `grep` on the run's own event log
(`data/runs/run_1788768588_5169/simulation_events.jsonl`) that the fired event is genuinely
`route_new_query`, not a coincidental different INFORMATION event.

Re-ran the 3 real worlds already shipping `information_source_profiles` — identical results to
the sibling persistence ticket's own earlier A/B check, confirming no regression from this second
fix either: `urban_political` grade=B events=1, `unit_information_source` grade=B events=1,
`unit_information_density` grade=A events=3.

## Files Changed
- `src/engine/pipeline_phases/information_intent_execution.py`
- `tests/unit/engine/test_information_intent_execution_phase.py`

## Completion Summary
`InformationIntentExecutionPhase.execute()` executed the raw `ActionIntent` it was handed but
never stripped it from `intent_results` afterward, letting it survive unchanged into
`entity.identity.latest_intent_results` and crash `StrategicWorkQueue.build()`'s unconditional
`.accepted` read. Minimal fix: filter it out of the entity's own `intent_results` before merging
in the real execution results. This was dormant, unexercised code — this ticket is the first time
it's ever run against a real `ActionIntent` in any corpus world, since the sibling persistence
ticket is what first made `route_new_query`/Branch 3 reachable at all. Unblocks
`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` to close DONE.
