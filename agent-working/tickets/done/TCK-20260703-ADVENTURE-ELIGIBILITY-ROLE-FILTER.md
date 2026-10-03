---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER
phase: done
date: 2026-07-03
tags: [ci, testing, adventure, strategic, parity]
---

# TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER

## Title
Wire two uncovered test directories into CI; fix AdventureDecisionPhase role-filter bug they surfaced

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Follow-up to TCK-20260702-CI-REQUIREMENTS-SPLIT (fixed CI's `pip install` failure). With CI
actually able to run again, an audit of `.github/workflows/test.yml` against every directory
under `tests/` found two test suites that no job — fast or slow — ever executes:

1. `tests/unit/systems/` (2 files) — omitted from every `tests/unit/*` job list; the one
   `tests/unit/*` subdirectory missing from all three unit jobs' explicit path lists.
2. `tests/simulation_quality/` (25 files, 404 tests) — not referenced by any job at all, and
   only 3 of its 25 files carry a `slow`/`extra_slow` marker, so even the whole-tree `slow` job
   never touches the other 22.

Wiring `tests/unit/systems` into CI immediately surfaced 2 real, currently-failing tests
(`TestLockHeldWhenThreatActive::test_lock_held_when_hp_high_but_hostile_present` and
`::test_lock_held_when_both_hp_low_and_hostile_present`), which trace to a genuine production
bug: `AdventureDecisionPhase.apply()`'s eligibility filter never checked entity role, contrary
to both its own docstring and the authoritative contract in
`docs/simulation/domains/adventure_contract.md` ("Role: `EntityRole = 0` (hero)"). Any
alive+active entity of any role (monster, shopkeeper, etc.) was eligible for hero routing.
The test failures were secondary — a `_make_hostile` fixture that didn't set `role=MONSTER`
was itself treated as a hero and produced a stray deferral update the test didn't expect.

`tests/simulation_quality` had no failures — 404 passed cleanly once run.

## Scope
- Add `tests/unit/systems` to the `unit-gameplay` job's pytest path list in
  `.github/workflows/test.yml`.
- Add a new `simulation-quality` job to `.github/workflows/test.yml` running
  `tests/simulation_quality`; add it to the `slow` job's `needs:` gate list.
- Fix `src/domains/adventure/phase.py`: add `e.identity.role == EntityRole.HERO` to the
  heroes eligibility filter, matching the documented contract.
- Fix `tests/unit/systems/test_spawn_lock_condition.py::_make_hostile`: set
  `role=EntityRole.MONSTER` so the fixture is semantically correct independent of the prod fix.
- Fix `tests/unit/observability/test_decision_trace.py::test_adventure_decision_phase_wires_writer`:
  its `MagicMock()` hero never set `identity.role`, so it silently stopped matching the
  (now-enforced) eligibility filter — added `hero.identity.role = EntityRole.HERO`.
- Add parity ledger entry `STRAT-243` in `docs/parity_ledger/strategic_cognition.yaml`.
- Bump `last_verified` in `docs/simulation/domains/adventure_contract.md` (doc was already
  correct; code was the one out of parity).

## Out of Scope
- `tests/unit/systems/test_spawn_lock_condition.py` and `test_quest_activation_pathway.py` are
  the only two files in `tests/unit/systems/`; no new test files added, just wired into CI.
- Two pre-existing, unrelated failures found while running the broader `unit-gameplay` lane
  (`tests/unit/social/test_group_lifecycle_fields.py::test_group_canonical_dict_has_no_missing_keys`
  and `tests/unit/movement/test_movement_spatial_regression.py::test_normal_move_triggers_oa`) —
  confirmed via `git stash` to predate this change and be unrelated to `AdventureDecisionPhase`.
  Not fixed here; flagged for separate investigation.
- Not auditing `phase.py:72`'s eligibility filter for any other undocumented gaps beyond role —
  alive/active/lock were already correctly enforced.

## Acceptance Criteria
- [x] `tests/unit/systems` runs in the `unit-gameplay` CI job
- [x] `tests/simulation_quality` runs in a new `simulation-quality` CI job
- [x] `simulation-quality` gates the `slow` job via `needs:`
- [x] `AdventureDecisionPhase.apply()` excludes non-hero entities from hero routing
- [x] All previously-hidden tests in both directories pass
- [x] No regression in any test file that imports/exercises `AdventureDecisionPhase`
- [x] Parity ledger entry added and doc `last_verified` bumped

## Related Tickets
- TCK-20260702-CI-REQUIREMENTS-SPLIT (prerequisite — fixed CI's install failure so this audit
  was possible)
- TCK-20260627-P2A-SPAWN-LOCK-COND (introduced `_threat_resolved` / the lock early-release path
  these tests cover; role-filter bug predates and is independent of that ticket's change)

## Related Docs
- `docs/simulation/domains/adventure_contract.md`
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-243)

## Related Stored Artifacts
- none (hotfix)

## Related Code Areas
- `.github/workflows/test.yml`
- `src/domains/adventure/phase.py:73-76`
- `tests/unit/systems/test_spawn_lock_condition.py`
- `tests/unit/observability/test_decision_trace.py`

## Assumptions / Open Questions
- Assumed the correct fix is to enforce the documented Role criterion in code (docs and the
  phase's own docstring agree) rather than relaxing the docs to match old code behavior —
  the doc was authoritative and unambiguous.

## Implementation Notes
1. `.github/workflows/test.yml`: added `tests/unit/systems \` to `unit-gameplay`'s pytest
   invocation. Added new `simulation-quality` job (checkout, setup-python, `pip install -r
   requirements.txt`, `pytest tests/simulation_quality -m "not slow" --tb=short -q`), and
   added `simulation-quality` to `slow` job's `needs:` list.
2. `src/domains/adventure/phase.py`: imported `EntityRole` from `src.core.enums`; changed the
   `heroes` list comprehension from `if e.combat.alive and e.lifecycle.active` to
   `if e.identity.role == EntityRole.HERO and e.combat.alive and e.lifecycle.active`.
3. `tests/unit/systems/test_spawn_lock_condition.py`: imported `EntityRole`; `_make_hostile`
   now calls `b.identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)`.
4. `tests/unit/observability/test_decision_trace.py`: imported `EntityRole`; the `MagicMock()`
   hero in `test_adventure_decision_phase_wires_writer` now sets
   `hero.identity.role = EntityRole.HERO` before use.
5. `docs/parity_ledger/strategic_cognition.yaml`: appended `STRAT-243` documenting the fix.
6. `docs/simulation/domains/adventure_contract.md`: bumped `last_verified: 2026-07-03`.

## Test Summary
```
pytest tests/unit/systems -q                                              # 18 passed
pytest tests/simulation_quality -m "not slow" -q                          # 387 passed, 19 deselected
pytest tests/perf/test_phase3_adventure_decision_budget.py \
       tests/unit/observability/test_event_extractor_agency2.py \
       tests/unit/observability/test_decision_trace.py \
       tests/unit/observability/test_event_extractor_social_faction.py \
       tests/integration/test_scenario_feature_flag_defaults.py \
       tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py \
       -m "not slow" -q                                                    # 148 passed
pytest tests/unit/strategic tests/unit/combat tests/unit/social tests/unit/economy \
       tests/unit/resource tests/unit/progression tests/unit/quest tests/unit/movement \
       tests/unit/faction tests/unit/motivation tests/unit/tactical tests/unit/campaigns \
       tests/unit/scenarios tests/unit/systems -m "not slow" -q
       # 1007 passed, 2 pre-existing unrelated failures (confirmed via git stash), 2 deselected
```

## Files Changed
- `.github/workflows/test.yml` — wired `tests/unit/systems` into `unit-gameplay`; added
  `simulation-quality` job; added it to `slow` job's `needs:`
- `src/domains/adventure/phase.py` — enforce `EntityRole.HERO` in eligibility filter
- `tests/unit/systems/test_spawn_lock_condition.py` — `_make_hostile` sets correct role
- `tests/unit/observability/test_decision_trace.py` — mock hero sets `identity.role`
- `docs/parity_ledger/strategic_cognition.yaml` — new `STRAT-243` entry
- `docs/simulation/domains/adventure_contract.md` — `last_verified` bump

## Completion Summary
Auditing CI coverage after the prior `requirements.txt` fix found two test directories
(`tests/unit/systems`, `tests/simulation_quality`) that no CI job — fast or slow — ever
executed. Wiring the first one in immediately surfaced a real production bug:
`AdventureDecisionPhase`'s hero-eligibility filter never checked `identity.role`, despite both
its own docstring and the authoritative `adventure_contract.md` requiring `EntityRole.HERO`.
Non-hero entities (e.g., monsters) could be routed through hero decision-making if alive and
active. Fixed the filter, fixed the two test fixtures that had been silently relying on the
missing check (a `_make_hostile` fixture and a `MagicMock` hero), added parity ledger entry
STRAT-243, and wired both directories into CI. `tests/simulation_quality` needed no fixes —
all 404 tests passed cleanly once given a job to run in. Two unrelated pre-existing failures
in `tests/unit/social` and `tests/unit/movement` were found and confirmed (via `git stash`)
to predate this work; left out of scope and flagged for separate follow-up.
