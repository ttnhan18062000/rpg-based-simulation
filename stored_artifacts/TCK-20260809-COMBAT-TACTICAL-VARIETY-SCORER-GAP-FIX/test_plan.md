---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX

## New tests (`tests/unit/observability/test_event_shapers.py`)

1. `test_combat_damage_carries_tactical_modifier_when_active` — a single active modifier
   (`FLANKING`) populates `combat_damage.payload["tactical_modifier"]` correctly.
2. `test_combat_damage_tactical_modifier_absent_when_no_trace` — an empty trace omits the
   `tactical_modifier` key entirely (not a null/empty placeholder).
3. `test_combat_damage_tactical_modifier_picks_mechanics_bible_order_when_multiple_active` —
   `BOND_SYNERGY` + `HIGH_GROUND` both active → `HIGH_GROUND` wins (earlier in the mechanics-bible
   table order).
4. `test_combat_damage_tactical_modifier_excludes_non_modifier_trace_keys` —
   `FINAL_ATK_MULT`/`REWARD_SOURCE`/`WOUND_INFLICTED` alone (no real modifier) → `tactical_modifier`
   omitted.

## Regression coverage

`tests/unit/observability/test_event_shapers.py`'s full existing suite (42 tests total) —
confirms the new `tactical_modifier` wiring doesn't change `combat_damage`'s own existing gate
condition or any other event's construction.
`tests/simulation_quality/test_combat_scorer.py` — confirms `CombatScorer`'s own real, pre-
existing `tactical_variety` handler scores correctly now that a real producer exists.

## Real corpus re-verification

A live `Kernel.tick_once()` loop, 2000 ticks, against `dungeon_crawl_seed42` under corpus-default
feature flags, run 3 times cleanly to characterize real, honest run-to-run variance (this
environment's own wall-clock-timing-dependent tick-budget/watchdog behavior causes genuine
non-determinism in exactly which ticks fire real combat, a pre-existing condition unrelated to
this fix). `combat_damage` itself fired 0/1/1 times across the 3 runs — sparse, matching its own
already-documented sparsity. On both runs where it fired, `tactical_modifier` was correctly
populated as `"STAMINA_EXHAUSTION"` — confirmed genuinely working live, not just via unit tests.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/observability/ tests/simulation_quality/test_combat_scorer.py -q`
