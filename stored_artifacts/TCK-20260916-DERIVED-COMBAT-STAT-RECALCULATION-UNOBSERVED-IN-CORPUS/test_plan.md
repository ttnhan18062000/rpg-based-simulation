---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS
artifact_type: test_plan
tags: [progression, simulation-quality, testing]
---

# Test Plan — TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS

This ticket is investigation-only; no production code changed. "Testing" here means the
methodology used to validate the measurement and the trace, not a new pytest suite. No new
permanent test file is added — the two ad hoc scripts below are one-off measurement instruments,
matching this epic's own established pattern for prior corpus measurements
(`TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`'s own original filing,
`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`).

## Instrument 1 — corpus measurement

A standalone script compiling `crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`
(seed 42) via the real `WorldCompiler`/`WorldRepository`, running each 1000 ticks through a real
`Kernel`, with `CombatRewardClassificationService.classify_defeated_target` wrapped to record every
real kill (tick, attacker, defender, xp_gain). Final per-entity `evolution_points`/`evolution_level`
read directly from `kernel.state`. Validated against the ticket's own prior positive control
(a direct `AttributeUpdate` reliably triggers `get_effective_stats`) by construction — this
instrument counts a different, more upstream signal (real kills), not `stats_dirty` calls, and its
own kill-count-vs-XP-total arithmetic was hand-checked against the printed per-kill records (e.g.
`crowded_frontier`'s 10 kills summing to exactly 100 XP, one entity's own 5 kills correctly summing
to 50).

## Instrument 2 — positive control, corrected mid-investigation

**First attempt (wrong layer, corrected before reporting):** `ApplyPath._apply_entity_update()`
called directly with a raw `EntityUpdate` — bypasses the real pipeline's `evolution` phase
entirely, producing a misleading "no level-up" result for combat-style XP.

**Second attempt (real pipeline, load-bearing result):** reused
`tests/mechanic_scenarios/test_action_pacing_readiness_gate.py`'s own world
(`mechanic_scenario_combat_judgement_withdrawal`) and staging pattern — a forced `ATTACK` task,
adjacent positioning, `Kernel(profile=PROD_SMALL, ...).tick_once()`. Two runs:
- Baseline: goblin at `evolution_points=0`, kills an orc worth 10 XP → `level=1, xp=10` (no
  level-up expected, none observed — confirms XP lands without over-claiming a level-up that
  shouldn't happen yet).
- Threshold-crossing: goblin pre-staged at `evolution_points=95`, same forced kill (+10 XP = 105,
  threshold 100) → `level=2, xp=5` — matches `docs/mechanics/attribute_progression_contract.md`'s
  own worked formula exactly (`105 - 100 = 5` carry-over). This is the decisive result: it proves
  the combat-XP-to-level-up chain works end-to-end through the real tick pipeline, ruling out the
  wiring-gap hypothesis the first (wrong-layer) control had suggested.

## Regression check

No `src/` code changed, so the standard scoped suite is a sanity check, not a regression gate for
new behavior:

```
.venv313/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry_completeness_check.py \
  tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_state_caller_check.py -q
```
→ 65 passed. Confirms the registry edits (`xp_leveling` → `partial`, new `evolution` binding
pointing outside the completeness checker's own `src/domains/`/`src/systems/` scope) did not shift
any pinned test count, matching the same outside-scope pattern already documented for
`declared_cognition_schema`/`committed_intentions` in the coverage-extension ticket.

`graphify-out/` was not moved aside and restored for this ticket — no `src/` or `tests/` file
changed, only `registries/mechanisms.yaml` (data) and `docs/brainstorm/rpg_feature_atlas.html`
(data), matching the same exemption already used for the mechanism-verification epic-folder
creation task.
