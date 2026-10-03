---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION

## Normal flow
- `test_readiness_regenerates_passively_per_tick`: an entity at 50.0 readiness with
  `readiness_speed=10.0` reaches 60.0 after one `ApplyPath.apply_generation` tick. Verified.
- `test_contextual_intruder_group_hostility_not_hardcoded_neutral`: a real
  `wild_beast_pack`→`hero_guild` attack, mutually engaged via `task.payload["target_id"]`, now
  resolves `LEGAL` (previously always `FRIENDLY_FIRE_ILLEGAL` regardless of engagement). Verified.

## Edge cases
- `test_readiness_regen_clamps_at_100`: an entity at 95.0 with `readiness_speed=10.0` clamps to
  100.0, not 105.0. Verified.
- `test_readiness_speed_zero_disables_regen`: `readiness_speed=0.0` leaves readiness unchanged
  (guards the `> 0` condition in the regen block, avoiding a no-op `replace()` call every tick for
  entities with regen disabled). Verified.

## Failure modes / regression-prone paths
- `test_readiness_speed_survives_to_readonly_reconstruction`: directly regresses the silent
  field-drop bug found in `EntityState.to_readonly()`'s hardcoded `CombatComponent` reconstruction
  — forces the `wounds`/`scars`-not-tuple branch and asserts `readiness_speed` survives. This is
  the single most important regression test in this ticket: without it, the whole readiness-regen
  fix would silently stop working on the very first tick for any entity whose combat component
  gets readonly-converted (which is most of them, per the real corpus probes).

## Real corpus re-verification (not unit-test-only)
- `is_attack_legal` probe (330 real samples methodology, `urban_political`): pre-fix 0% legal,
  100% illegal (55% `INSUFFICIENT_READINESS`, 45% `FRIENDLY_FIRE_ILLEGAL`).
- Same probe, `dungeon_crawl`, 600-tick run, post-fix: legal rate 1.3% (2/159 real-hostile
  samples) — real, non-zero, honestly reported as partial not full improvement.
- `readiness_speed` sweep (10/20/30/50, `dungeon_crawl`): confirms no single value in this range
  is clearly superior; `10.0` shipped as the evidence-grounded-but-modest default.

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/combat/ tests/unit/movement/ tests/unit/core/ \
  tests/unit/kernel/ tests/unit/optimization/ tests/unit/content/ tests/unit/engine/ \
  tests/unit/progression/ tests/unit/tactical/ -q -m "not slow"
.venv/bin/python3 -m pytest tests/integration/combat/ tests/integration/pipeline/ \
  tests/integration/kernel/test_determinism_suite.py tests/integration/kernel/test_seed_stability.py \
  tests/integration/kernel/test_authoritative_outcome_truth.py -q -m "not slow"
```
Result: 1 pre-existing failure (`tests/unit/movement/test_movement_spatial_regression.py::
test_normal_move_triggers_oa`), confirmed via `git stash` bisection to fail identically on the
pristine pre-ticket codebase — not caused by this ticket's changes, out of scope to fix here. All
other tests pass (960 unit + 127 integration, in the scoped run).
