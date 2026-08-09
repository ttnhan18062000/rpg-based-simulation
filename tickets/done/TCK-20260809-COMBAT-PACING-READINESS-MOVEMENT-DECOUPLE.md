---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE

## Title
Movement double-costed both `readiness` and `stamina` for the same fatigue concern — the real,
previously-deferred cause capping the real attack-legal rate at ~1.3% even after this session's
own readiness-regen and friendly-fire fixes; removing the double-cost raises it to a real,
measured 28.5-36.6%

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct follow-up to `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` (same
session), whose own §2.36 divergence entry explicitly disclosed and deferred this exact gap. The
user's own follow-up request ("focus into a complete combat component") made this the natural
next real target — the biggest remaining structural blocker to the combat-outcome-diversity work
landed earlier this session actually mattering at real, observable volume.

**Root cause**: `MovementSystem.resolve_move()` (`src/engine/movement.py`) and the position-swap
path (`src/engine/pipeline_phases/movement.py`) both applied a real `readiness_delta` cost to
every successful move, in addition to the real, separate, already-existing `stamina` cost
(`StaminaComponent.MOVE_COST`, its own regen and exhaustion mechanic,
`docs/combat/combat_movement_overhaul_spec.md` §5). `readiness`'s own documented contract
(`docs/engine/contracts/minimal_kernel.md` §5) is a pure attack-eligibility/cooldown gate, not a
movement-fatigue resource — `stamina` already filled that role independently. This meant any
entity that had to travel to reach a hostile arrived readiness-depleted even with passive
readiness regeneration active (the sibling ticket's own fix), regardless of tuning.

## Scope
1. Confirm the double-cost via direct source read (not assumed).
2. Remove the redundant `readiness_delta` cost from both real movement-application sites, leaving
   `stamina` as the sole movement-fatigue cost.
3. Re-verify against real corpus data using the same `is_attack_legal` probe methodology this
   whole session's combat investigation chain has used.

## Out of Scope
- Redesigning `verify_movement_legality()`'s own smaller readiness pre-check (a real, correct,
  much smaller post-attack movement lockout, not part of the double-cost bug).
- The now-dominant `OUT_OF_RANGE` illegal reason (a real, much smaller-magnitude remaining lead —
  pursuit/approach pacing — not a structural blocker of the scale readiness was).
- `ActionStyle`/personality-driven combat-outcome work (already landed, sibling tickets this
  session).

## Acceptance Criteria
- [x] investigation.md confirms the real double-cost root cause via direct source read
- [x] Fix re-verified against real corpus data (not assumed): `dungeon_crawl`/`urban_political`
- [x] No regressions across the full combat/movement/entity-generation test surface
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION (DONE, same session — the
  ticket whose own §2.36 divergence entry first found and explicitly deferred this exact gap)
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION, TCK-20260809-COMBAT-ACTIONSTYLE-WIRING (DONE,
  same session — the combat-outcome-diversity work this fix makes actually observable at real
  volume, since combat now resolves far more often)

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 (corrected)
- `docs/combat/combat_movement_overhaul_spec.md` §5 (the real, pre-existing stamina-fatigue spec
  this fix aligns readiness back toward)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/movement.py` (`MovementSystem.resolve_move`)
- `src/engine/pipeline_phases/movement.py` (`_build_position_swap_entity_update`)
- `src/engine/legality.py` (`LegalityServiceV2.verify_movement_legality`, left untouched)

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Removed `readiness_delta=-readiness_cost if success else 0.0` (and its own now-dead
`readiness_cost`/`terrain_cost` computation) from `MovementSystem.resolve_move()`
(`src/engine/movement.py`), and `readiness_delta=-entity.combat.move_cost` from the position-swap
path (`src/engine/pipeline_phases/movement.py`). Both sites retain their real, unchanged stamina
cost. `verify_movement_legality()`'s own separate, smaller readiness pre-check
(`readiness >= move_cost`) was deliberately left untouched — it still provides a real, correct,
brief movement lockout immediately after an attack resets readiness to 0.

Real re-verification (same `is_attack_legal` probe methodology used throughout this session):
`dungeon_crawl` (600 real ticks) moved from 1.3% legal to **28.5%** legal; `urban_political` (600
real ticks) showed **36.6%** legal. `INSUFFICIENT_READINESS` no longer appears at all in either
world's own real reason-code breakdown — the remaining illegal reasons are `OUT_OF_RANGE` (now
dominant, expected given random-sample timing mid-approach) and `FRIENDLY_FIRE_ILLEGAL`.

## Test Summary
New/extended tests: `test_successful_move_no_longer_costs_readiness`
(`tests/unit/movement/test_phase4_movement.py`), and `test_mutual_adjacent_position_swap_succeeds`
extended with a readiness-unchanged assertion (`tests/unit/movement/test_position_swap.py`). Full
scoped pytest across `tests/unit/movement/`, `tests/unit/combat/`, `tests/unit/core/`,
`tests/unit/kernel/`, `tests/unit/tactical/`, `tests/unit/optimization/`,
`tests/unit/worldbuilding/`, `tests/unit/worldassembly/`, `tests/unit/strategic/`,
`tests/unit/entities/`, `tests/unit/content/`, `tests/unit/resource/`, `tests/unit/social/`, plus
integration combat/pipeline/determinism suites: 1453+ passed, 3 pre-existing failures (2 already
confirmed unrelated earlier this session, plus a newly-encountered third,
`test_registries.py::test_referential_integrity`, confirmed via `git stash` bisection to be
unrelated to this ticket's own changes — a real, separate, similar-class test-isolation issue
not fixed here). Zero new regressions from this ticket's own changes.

## Files Changed
- `src/engine/movement.py` — removed movement's readiness cost.
- `src/engine/pipeline_phases/movement.py` — removed the position-swap path's readiness cost.
- `tests/unit/movement/test_phase4_movement.py` — new test.
- `tests/unit/movement/test_position_swap.py` — extended existing test.
- `docs/mechanics/02_combat_laws.md`, `docs/parity_ledger/combat_movement.yaml`,
  `docs/guidelines/intentional_divergences.md` — updated.

## Completion Summary
Closed the deepest, previously-explicitly-deferred gap in this session's own combat-legality
investigation chain: movement was silently double-costing both readiness and stamina for the same
real fatigue concern, structurally capping the real attack-legal rate regardless of how the
readiness-regen mechanism itself was tuned. Removing the redundant cost (stamina already,
independently serves the movement-fatigue role) raised the real, measured attack-legal rate from
1.3% to 28.5-36.6% on live corpus worlds — a genuine, verified, order-of-magnitude improvement
that makes this session's earlier combat-outcome-diversity work (race-correlated bravery,
ActionStyle wiring) actually observable at real volume during a simulation run.
