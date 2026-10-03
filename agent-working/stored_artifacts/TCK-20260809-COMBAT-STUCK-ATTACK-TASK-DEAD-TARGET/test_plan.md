---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET

## New tests (`tests/unit/actions/test_action_routing_task_reset.py`)

1. `test_attack_against_dead_target_resets_task_to_idle` — `ATTACK` against a target with
   `combat.alive=False`/`lifecycle.active=False` resets `task.payload_set` to `{}`.
2. `test_attack_against_incapacitated_but_alive_target_resets_task_to_idle` — confirms the reset
   isn't narrowly tied to `combat.alive` specifically (`lifecycle.active=False` alone also
   triggers `TARGET_INCAPACITATED`).
3. `test_attack_with_insufficient_readiness_does_not_reset_task` — a recoverable failure
   (`INSUFFICIENT_READINESS`) preserves the original payload/`target_id` unchanged.
4. `test_attack_out_of_range_does_not_reset_task` — a recoverable failure (`OUT_OF_RANGE`)
   preserves the original payload/`target_id` unchanged.
5. `test_missing_action_kind_is_untouched` — a task update with no real `action` key is skipped
   entirely by `route()`'s own pre-existing short-circuit, confirming this fix's new condition
   isn't evaluated for non-action task updates.

## Regression coverage

Full scoped re-run: `tests/unit/actions/ tests/unit/combat/ tests/unit/tactical/
tests/unit/movement/ tests/unit/kernel/` — confirms the existing `EAT`/`REST`/`SLEEP`-success
reset pattern this fix's own new condition is OR'd alongside remains byte-identical (the change
is purely additive, no existing condition altered), and no other real behavior in the touched
pipeline phase regressed.

## Real corpus re-verification

A live `Kernel.tick_once()` loop, 2000 ticks, against `dungeon_crawl_seed42` under corpus-default
feature flags, run 3 times cleanly to characterize real, honest variance (matching this session's
own established methodology). `TARGET_INCAPACITATED` volume: pre-fix baseline 128/144 occurrences
(one stuck attacker/dead-target pair repeating for a real 180+-tick span); post-fix, exactly 4
occurrences per run (2 distinct pairs × 2 legitimate same-tick dispatches each, matching the
disclosed, confirmed-legitimate 2-pass Collection/action_routing architecture) — a genuine,
consistent ~35x real reduction across all 3 re-runs.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/actions/ tests/unit/combat/ tests/unit/tactical/ tests/unit/movement/ tests/unit/kernel/ -q`
