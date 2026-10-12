---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6
phase: planning
date: 2026-10-09
tags: []
---

# TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6

## Title
A starvation death writes a typed record of the food ways the subject's last decisions judged open and in reach, and the ways it attempted (M0 gate H6).

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The M0 gate (roadmap section 12, designer memo row 54) has the hard check H6: "No starvation with an untried way in reach." No trace records it today. Starvation shows only as HP loss without attacker_id (src/observability/event_extractor.py). The designer ruled (2026-10-09, owner-confirmed) that this record must exist BEFORE the go/no-go run on the free-meal-OFF arm, inside the parked removal stack (d27-removal-stack-batch2) or as its own ticket directly in front of it. It must never trail the removal.

## Scope
- A typed starvation-death record, written at the authoritative death apply. Fields: subject id, kind, tick, the ways judged open and in reach by the subject's last N decisions, and the ways attempted. Way ids come from the SURV-06 way set (gather/forage, hunt+eat raw, buy, receive), as typed enums, not reason strings.
- DEATH CAUSE (designer, 2026-10-10): the record keys off the STARVATION STEP itself, i.e. the typed source of the last HP loss, never "no attacker" or "hunger >= 95". apply.py (~line 120) mislabels sleep-deprivation-drain deaths as STARVATION; Lane C's cause-label fix comes first.
- It covers every kind (D42), with ways per the kind's diet.
- TWO COLUMNS per way (memo row 56, owner-confirmed): (a) the ways the subject's pull judged open and in reach; (b) the ways truly in reach on the world state. H6 is judged on (a): a way the pull saw and never attempted. Rows where (b) has a way that (a) lacks are reported at R-level as "unknown to the subject" and fail nothing. Until M1's honest-perception child lands, (a) is true-map, so the difference is empty; that is disclosed and expected.
- Depends on TCK-20261009-THE-HUNGER-PULL-AIMS-AT-THE-NEAREST-OPEN-WAY-NOT-THE-INN-SURV-07 (column (a) must come from the fixed pull).
- Inspection: it is readable from run output by the gate aggregator. Tests: normal flow, a death with an untried in-reach way, a death with every way tried, and a kind with a diet-restricted way set.

## Out of Scope
- The free-meal removal itself (the parked stack).
- Any change to need-pull or way-selection behaviour; the record is observational only.

## Acceptance Criteria
- Every starvation death in a run has exactly one record. The H6 query (deaths where a way was judged open and in reach and never attempted, among broke workers) runs from records alone.
- The record is typed, serialises, and is deterministic across two runs.
- If it touches state.py, apply.py or another Phase B held file, it waits for perf's Phase B merge and asks rpg-planner before adding a field.

## Related Tickets
Parked free-meal removal (d27-removal-stack-batch2). TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02 (merged in #457, as D36).

## Related Docs
docs/world_rules (SURV-02, SURV-06, SURV-07); roadmap section 12; designer memo rows 52-54.

## Related Stored Artifacts
agent-working/staging_artifacts/TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
src/observability/event_extractor.py, the starvation apply path (D36 staged starvation), and the need-pull way enumeration (SURV-07).

## Assumptions / Open Questions
- ANSWERED in investigation.md: the per-decision way set is LOCAL (computed in the goal scorers, then discarded; only a debug log line keeps the chosen and rejected utilities). The plan keeps no new authoritative state: see plan.md (decision pending rpg-planner).
- (original question) Where the per-decision "open and in reach" set is computed today, and whether it is kept or only local to the decision. If it's local, the record needs a bounded per-subject trail, which is a durable-state question for rpg-planner.

## Implementation Notes
Owner lane: Lane B (rpg-implementer-2), with the removal stack. Built as Option A with rpg-planner's five amendments (plan.md).
- `src/ai/goals/ways.py`: `WayKind` (str Enum: CARRIED_FOOD, INN_MEAL, FORAGE, SCAVENGE, HUNT_EAT_RAW, BUY, WORK_SHIFT, RECEIVE) and the pure `ways_in_reach(entity, state)`. Placed in `src/ai/goals` (not `src/observability`, as the plan said) so the scorer and the record share it without `ai` importing `observability`. The scorer's inn test is now `inn_in_reach`, and `shop_sale_in_reach`/`work_in_reach`/`open_food_step_kinds` are shared with `opening_steps`. Diet gates apply (D44): a meat-only body lists no plant, prepared-food or inn way. RECEIVE is declared and never returned.
- `src/observability/starvation_record.py`: frozen `StarvationDeathRecord`, and `StarvationRecorder` with class-level bounded per-subject trail (union of ways judged open on strategic re-decision ticks while hungry enough to escalate, ways attempted from the resolver's accepted/rejected transfers, reset on a meal), cleared by `reset_run_state()`. Keyed off `PassiveDeathCause.STARVATION` with `passive_death_cause_tick == tick`. `_judged_ways` is the one seam M1's honest-perception child will split from the true map; a test pins (a) == (b) until then.
- `src/observability/run_state.py`: `reset_run_state(strategic_cadence)` and `extract_events(...)` are what the kernel calls (it replaced five reset lines in the kernel's init, so the kernel and the extractor grew by 0 lines under the ratchet). The recorder runs beside, not inside, `EventExtractor.extract`; `extract_events` returns nothing from the recorder when the mode is OFF.
- NO-DATA: a `starvation_channel_live` header opens the run; `EventRecorder.closing_event_sources` (registered by the recorder) writes a `starvation_channel_tally` (deaths seen, records emitted) at `EventRecorder.shutdown()` only for a recorder that saw the header. Amendment 3: the pressure modes DEGRADED and PRESSURE drop or sample INFO events, so the record, header and tally are severity WARNING; SURVIVAL drops everything, and the tally then exceeds the records (the no-data signal). The metric module maps not-live to `harness_error`.
- No state.py, apply.py or other Phase B file is touched.

## Test Summary
`tests/unit/observability/test_starvation_death_record.py`: 14 tests (untried way in reach; every way tried; union keeps an earlier-open way; a meal resets; diet-restricted kind; one record per death; non-starvation or earlier cause tick writes none; (a)==(b) pin; two-run determinism; header and tally; OFF mode has no header; reset clears; a real Kernel run with one record, the header, WARNING severity and the shutdown tally; a meat-eater with prey and a carcass lists HUNT_EAT_RAW and SCAVENGE and no plant or inn way). Also green: tests/unit/ai (93 with the new file), tests/unit/observability + tests/unit/engine (1665 passed, 4 skipped), the mechanism pin test (scope 335, unbound 247). Ratchet OK (0 new, 0 worse); mypy baseline clean.

## Files Changed
src/ai/goals/{ways,opening_steps,scorers}.py; src/observability/{starvation_record,run_state,event_recorder}.py; src/engine/kernel.py; tests/unit/observability/test_starvation_death_record.py; tests/unit/tools/test_mechanism_registry_completeness_check.py (pins)

## Completion Summary
TBD
