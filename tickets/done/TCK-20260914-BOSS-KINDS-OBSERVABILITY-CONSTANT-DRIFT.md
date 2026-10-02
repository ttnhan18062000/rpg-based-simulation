---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT
phase: done
date: 2026-09-14
tags: [observability, world]
---

# TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT

## Title
Two supposedly-parallel `_BOSS_KINDS` constants have silently drifted apart — `event_shapers.py`'s
copy is missing `"dragonkin"`, which `event_extractor.py`'s copy includes — meaning Lair-occupant
kills may be classified differently by two observability code paths that should agree

## Status
DONE

## Tier
standard


## Type
bug

## Priority
P3

## Request Summary
Found while investigating `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s Finding 4/5.
`src/observability/event_shapers.py` defines `_BOSS_KINDS = frozenset(("world_boss",
"ancient_sentinel"))`. `src/observability/event_extractor.py` defines its own separate
`_BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel", "dragonkin"))`. These two constants
share a name and an obvious intent (classify which entity kinds count as "boss" for observability
purposes) but have drifted apart — one recognizes `dragonkin` (the Lair-occupant kind spawned by
`check_for_lair_spawn()` in `src/world/boss.py`) as a boss kind, the other does not.

Lower stakes than the gameplay-facing defects in the sibling ticket (this affects event
classification/telemetry shape, not the encounter itself), but it's a real, concrete instance of
the same "two things that should stay identical didn't" pattern — worth fixing on its own since it's
small and independent of any fix decision the sibling ticket is waiting on.

## Scope
Scope refreshed 2026-10-02 after `rpg-feature-planning` confirmed it is non-RPG, telemetry-only (the boss set is
declared authoritatively in `src/world/boss.py`, which spawns `ancient_sentinel`, `world_boss` and
`dragonkin`; `event_extractor.py` already classifies all three, so `event_shapers.py` is lagging).
There are four divergent sites in two different concepts, not two (names are used here, not line numbers, which drift):
- Boss-kind set: extractor `_BOSS_KINDS` = {world_boss, ancient_sentinel, dragonkin} (correct); shapers `_BOSS_KINDS` = {world_boss, ancient_sentinel} (missing `dragonkin`).
- Inline exclusion tuple: extractor = {world_boss, ancient_sentinel, goblin_raider, dragonkin}; shapers = {world_boss, ancient_sentinel, goblin_raider} (missing `dragonkin`). This is a **different set serving a different purpose**: it contains `goblin_raider`, which is in neither `_BOSS_KINDS`.
- Direction: `event_shapers.py` converges to `event_extractor.py` by adding `dragonkin` to both of its sets. Do not touch the extractor's sets and do not remove `dragonkin` anywhere.
- Do **not** merge the boss set and the exclusion tuple into one constant: that would pull `goblin_raider` into the boss set, an RPG-visible classification change that belongs to `rpg-feature-planning`. Keeping both separate is mandatory; sharing one constant per concept is allowed, if architecture review prefers it, as long as the two concepts stay distinct.
- Decision 2026-10-02 (user, after `rpg-feature-planning`'s suggestion; reviewer agrees): **one constant per concept, defined once**, in a new leaf module under `src/observability/` (e.g. `src/observability/entity_kind_constants.py`), with the extractor's current membership, imported by BOTH `event_shapers.py` and `event_extractor.py`. The extractor edit replaces its inline set/tuple literals with imports of constants whose membership is byte-identical (rpg-feature-planning confirmed this reading of "never touch the extractor's sets" as membership). Do not put the constants in `event_extractor.py` (the rollback path should not own the taxonomy) or in observability config. A comment names `src/world/boss.py`'s `check_for_lair_spawn()`/`check_for_boss_spawn()` as the canonical producer and says the observability home is a deliberate interim. Source-text/AST parsing in the test is rejected (it pins spelling, not behaviour).
- A regression test asserts the membership itself (`dragonkin` in both the boss set and the exclusion tuple; `goblin_raider` in the exclusion tuple and NOT in the boss set) and that both modules use the same constant objects, referencing the constants, not line numbers.
- Before Implement, the plan lists every event-count and recorded-hash fixture and every SimQ scorer keyed on `boss_spawned` or `spawned_count` that could move, and this ticket says so. If any recorded expectation (fixture, hash, baseline) changes, report it: do not quietly absorb it and do not re-record a hash or baseline to make a gate pass (`docs/testing/regression_policy.md` §13); show the doc/ledger change before the test change (Epic C criterion 4), and a moved fixture is a `docs/parity_ledger/infrastructure.yaml` touch.
- Small, targeted fix: do not restructure the observability event-shaping pipeline beyond this.

## Out of Scope
- The maturity/trauma gate reachability question, and the tier-5/loot defects — tracked in the
  sibling ticket, not this one.
- Any other observability constant beyond these two pairs.
- Claiming that `dragonkin` spawns or produces events in corpus runs: unmeasured; this ticket claims consistency only.
- Changing the extractor's sets, or moving `goblin_raider` into the boss set.

## Acceptance Criteria
- [x] The shapers' boss-kind set and the extractor's boss-kind set have identical membership, and the shapers' inline exclusion tuple and the extractor's have identical membership.
- [x] `goblin_raider` is not in either boss-kind set after the change.
- [x] A test pins both concepts so that drift in either fails it, by asserting membership and shared constant objects; it fails on the pre-fix shapers.
- [x] The plan names the fixtures/hashes/scorers that could move, and the run reports whether any moved (if none, that is stated).

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)

## Related Docs
- None yet.

## Related Stored Artifacts
Standard tier: `staging_artifacts/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT/` (moved to `stored_artifacts/` at Finalize).

## Related Code Areas
- `src/observability/event_shapers.py` (`_BOSS_KINDS`)
- `src/observability/event_extractor.py` (`_BOSS_KINDS`)
- `src/world/boss.py` (`check_for_lair_spawn()`, the real producer of `dragonkin` entities)

## Assumptions / Open Questions
- Re-tiered from hotfix to standard on 2026-10-02. Tier chosen by test-architecture to reach Architecture-Verify: `implement-ticket.js` skips Review and Architecture-Verify for hotfix, and this run is the vehicle for Epic C criterion 2 (does the architecture-reviewer test-quality checklist run unprompted when a diff changes tests). This is not a claim that the pipeline picked the phase itself, and it is not a judgement that the change needs a plan review on its own merits.
- Run context: this is the real `/implement-ticket` run for Epic C criterion 2 (`TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING`). The orchestrator prompt is unmodified, with no added checklist sentence; verdicts are recorded exactly as emitted. A copy of this ticket under `tests/fixtures/open_ticket_overlap/corpus/todos/` is a fixture and must not be edited when this ticket closes.
- Whether any other entity kind besides `dragonkin` is missing from one list and not the other was
  not exhaustively checked here — only the one confirmed discrepancy is documented; whoever picks
  this up should diff the two full sets, not just add `dragonkin`.

## Implementation Notes
Implemented per plan.md with no deviations: new leaf module; `WorldDynamicsShaper._BOSS_KINDS = BOSS_ENTITY_KINDS` alias keeps object identity; extractor's function-local set and inline tuple replaced by imports (membership byte-identical); two dragonkin shaper tests plus `test_entity_kind_constants.py` (identity/membership, no AST parsing). Ledger WORLD-109 follow-up-gap text replaced, WORLD-115 got an update note; coverage rows updated.

Live-path consequence (from `rpg-feature-planning`, 2026-10-02; relayed, to be verified by Investigate): both boss blocks are gated on `_push_shapers_phase2_active`. The shaper (live, default-on via `ENABLE_PUSH_EVENT_SHAPERS`) is the path that emits, and it is the copy MISSING `dragonkin`; the extractor block (rollback, runs only when the flag is NOT active) already has it. So this is not symmetric bookkeeping between two live paths: it fixes a live default-path telemetry gap. After the change, `dragonkin` spawns newly emit `boss_spawned` + `narrative_milestone` (`first_boss_spawned`) on the default path and leave `spawn_cadence_fired`'s `spawned_count`. This changes emitted output. `goblin_raider` has its own `elif` branch (`raid_party_spawned`) and must stay out of the boss set. Whether `dragonkin` spawns in corpus runs is unmeasured (spawn is gated on maturity and region trauma, `src/world/boss.py`); "hard to reach" is not "cannot happen", and this ticket claims consistency and the live-path fix, not observed events.

Architecture-Verify evidence and shadow finding (2026-10-02): the production architecture-reviewer returned `APPROVED` with a `notes` string containing "test_quality_findings: none (test files were not read in depth; clean advisory)". The advisory shadow reviewer (claude-fable-5-1, never read by the gate) returned one structured advisory test-quality finding: the identity test `test_spawn_cadence_exclusion_is_one_object_with_expected_membership` proves the shaper module imports the constant, not that `shape()` consults it; behavioural coverage is `test_dragonkin_is_excluded_from_spawn_cadence_count` in `test_event_shapers_world_dynamics.py`, which drives a real `WorldDynamicsShaper().shape()` call. **Disposition: declined, no action required** (the behavioural test exists and would fail on a stale tuple). Verbatim records are in this ticket's stored artifacts. Cost, observational (subagent tokens as reported, orchestrator context excluded): final pass 742,229 across 12 agents including the advisory shadow review (51,917); first pass to the Plan gate 176,589 across 3 agents; total 918,818.

## Test Summary
Red first: 4 new tests failed on pre-fix shapers (identity and dragonkin behaviour). After the change: `tests/unit/observability`, `tests/simulation_quality/test_world_dynamics_scorer.py`, `test_scenario_coverage.py`, `test_grade_regression.py`, `tests/architecture/test_phase19_observability_boundaries.py`, `test_phase18_import_boundaries.py`, `tests/integration/observability/test_kernel_event_recording.py`: 1162 passed, 83 skipped. No recorded fixture, hash, baseline or scorer expectation moved (none re-recorded).

## Files Changed
- src/observability/entity_kind_constants.py (new)
- src/observability/event_shapers.py
- src/observability/event_extractor.py
- tests/unit/observability/test_entity_kind_constants.py (new)
- tests/unit/observability/test_event_shapers_world_dynamics.py
- docs/parity_ledger/world_dynamics.yaml (WORLD-109, WORLD-115)
- docs/simulation_quality/event_type_coverage.md
- staging_artifacts/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT/investigation.md
- staging_artifacts/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT/plan.md
- staging_artifacts/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT/test_plan.md
- tickets/done/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT.md

## Completion Summary
The boss-kind set and spawn-cadence exclusion tuple are now defined once in `src/observability/entity_kind_constants.py` (BOSS_ENTITY_KINDS, SPAWN_CADENCE_EXCLUDED_KINDS) with the extractor's prior membership, and imported by both `event_extractor.py` (membership unchanged) and `event_shapers.py` (gains dragonkin in both). On the live default path dragonkin spawns now emit boss_spawned and narrative_milestone and leave spawn_cadence_fired.spawned_count. Tests pin identity and membership; WORLD-109/WORLD-115 and the event coverage doc were updated.
