---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED
phase: open
date: 2026-10-22
tags: [testing]
---

# TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED

## Title
An rpg gate known entry can name the (world, seed) it owns, so owning one known validity fail does not hide every other fail of the same metric

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner: testing-planner (tools/test_architecture/**). Filed by rpg-planner for testing.

`tools/test_architecture/rpg_gate_known.yaml` entries match only `<metric_id>[:<group>]` (`known_reds.RPG_GATE_SPEC`, `rpg_gate_candidate._omissions` via `known_reds.owner_of(metric_test_id(...))`). The v1 validity rows are run rows with group `*`, so an entry cannot say which (world, seed) it owns. At v1 the owner accepted exactly three V3 known reds (urban_political/44 merchant 28 t3140; crowded_frontier/46 raider 38 t3778; frontier_living_world/44 worker 2 t3736; cutoff 2026-10-21), but the only expressible entry is a blanket `match: "V3"`, which also owns any NEW starvation death on any world or seed until it expires. The user accepted that breadth with expires_on 2026-11-05 and manual checks of each gate report (#715 comment 6337993346). The existing V1 free-meal entry has the same breadth.

## Scope
1. Optional `world` and `seeds` (or a `cases` list of {world, seed, entity_id}) on an `rpg_gate_known.yaml` entry; the matcher owns a validity fail only when its (world, seed) (and, if given, the example entity ids) are covered. Unscoped entries keep today's meaning.
2. `rpg_gate_candidate` omits only the covered (world, seed) rows; an uncovered fail of the same metric stays unowned (refuses the candidate; RED in the report).
3. Lint: shadowing rules extended to scoped entries; tests in tests/unit/tools/test_known_reds.py and the candidate/report tests.
4. Replace the blanket V3 entry with three scoped entries (each with its own ticket: N14 -> TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT, N15 x2 -> TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE), before 2026-11-05.

## Out of Scope
Changing which reds are accepted (owner); rpg simulation fixes.

## Acceptance Criteria
- A gate run with a fourth V3 fail on an uncovered (world, seed) reports it RED/unowned while the three scoped ones stay owned.
- Existing V1 entry behaviour unchanged unless scoped deliberately.
- Lands before the blanket V3 entry expires (2026-11-05).

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1; TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE.

## Related Docs
docs/plans/systemic_world/v1_disclosure.md (M5); docs/plans/systemic_world/owner_decision_memo.md.

## Related Stored Artifacts

## Related Code Areas
tools/test_architecture/known_reds.py; tools/test_architecture/rpg_gate_candidate.py; tools/test_architecture/rpg_gate_report.py; tools/test_architecture/rpg_gate_known.yaml.

## Assumptions / Open Questions
- Testing decides the schema shape (world/seeds vs cases). RULED by testing-planner, 2026-10-23:
  - **Shape: an optional `cases` list** on an `rpg_gate_known.yaml` entry, each case `{world, seed, entity_id?}`. `world` and `seed` are required. `entity_id` is optional: give it when that metric's examples carry `entity_id` (V3 does, via `_check_untried_way`); leave it out for rows whose examples have none, and the case then owns every fail of that row on that (world, seed). There is no separate `world`/`seeds` field form, so there is one way to scope.
  - `cases` is allowed only on `state: fail` entries. A drift entry with `cases` is a lint error.
  - **Matching** (a finding-aware matcher next to `owner_of`, e.g. `owner_of_finding(finding, known, state)`; `owner_of` keeps its string meaning for the slow registry):
    1. An unscoped entry matches as today.
    2. A scoped entry owns a fail only if it is a run-scope finding whose (world, seed) is one of its cases. When the matching cases give entity ids, the finding must also satisfy `violations == len(examples)` (no example was cut by the module's `MAX_EXAMPLES` cap), and every example's `entity_id` must be one of the case ids for that (world, seed).
    3. A fail that can't be verified is not owned: more violations than examples, an example with no `entity_id` where the case names one, or an unexpected id. Nothing is assumed.
    4. A scoped entry never owns a pooled-scope fail.
    5. A scoped entry whose pattern matches but whose cases don't cover the finding does not stop the search. The next entry is tried, so several scoped entries can share one `match` (needed for N14 vs N15, which have different tickets).
  - **Lint:**
    - an unscoped entry placed before a scoped entry with the same pattern shadows it (error);
    - two entries whose cases overlap on (world, seed[, entity_id]) are an error;
    - a case missing `world` or `seed`, or with an unknown key, is an error;
    - `cases: []` is an error.
  - **Candidate:** `_omissions` calls the finding-aware matcher with the row's world, seed, violations and examples. It omits the (world, id, group) row only when every failing seed of that world is covered. Any uncovered seed refuses, as today.
  - **Report:** `_ownership` uses the same matcher on its findings, which already carry world, seed and examples. `stale_known_entries` reports a scoped entry as stale per uncovered case: a case that no longer fails is listed by its world/seed/entity.
  - **The v1 entries:** replace the blanket `match: "V3"` with TWO scoped entries, one per owning ticket:
    - N14: `cases: [{world: urban_political, seed: 44, entity_id: 28}]` -> TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT;
    - N15: `cases: [{world: crowded_frontier, seed: 46, entity_id: 38}, {world: frontier_living_world, seed: 44, entity_id: 2}]` -> TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE.

    Before committing, confirm the world names and entity ids against the docs of a green v1 gate run (39799337778 on e8df8b96d). If any differs from v1_disclosure.md M5, stop and ask rpg-planner. Keep `expires_on` at 2026-11-05 unless rpg-planner and the owner re-rule it. The V1 entry stays unscoped (AC2).
  - Test cases on top of the ACs:
    - a fourth V3 fail on an uncovered (world, seed) is RED/unowned and refuses the candidate (AC1);
    - a covered (world, seed) with a NEW entity id is unowned;
    - violations above the examples cap is unowned;
    - a pooled V3 fail is unowned under scoped entries;
    - the overlap lint and the shadow lint;
    - the slow registry (SLOW_SPEC) is unchanged and rejects `cases`.
  - Docs: the format doc (`docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`) and the `rpg_gate_known.yaml` header describe `cases`.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
