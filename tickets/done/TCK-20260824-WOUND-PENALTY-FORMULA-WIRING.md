---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-WOUND-PENALTY-FORMULA-WIRING
phase: done
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-WOUND-PENALTY-FORMULA-WIRING

## Title
Wire In the Severity-Scaled Wound/Scar Penalty Formula

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
The severity-scaled penalty formula originally described for wounds/scars is dead code; live combat instead applies a flat penalty=5.0 to attack/defense only. The author wants the severity-scaled formula wired in for real, replacing the flat placeholder.

## Scope
- Change combat.py's `_get_wound_infliction()` to construct a `WoundState` via `WoundService.create_wound()` instead of the current hardcoded flat penalty=5.0 (combat.py:604-622)
- Ensure the live path produces `atk_penalty=int(severity*3)`, `def_penalty=int(severity*2)`, `speed_penalty=int(severity*2)`, `max_hp_penalty=int(severity*10)`
- Ensure `wound.max_hp_penalty` (currently always 0) becomes non-zero and reduces effective max_hp for severe wounds
- Add a test asserting two wounds of different severity produce measurably different penalties through the live path
- Correct `docs/mechanics/01_entity_anatomy.md:117` and `docs/mechanics/02_combat_laws.md:77` (currently document the flat -5/-5 bug) and `docs/parity_ledger/combat_movement.yaml` COMB-072/073/102/103/104 to reflect the real live-wired formula

## Out of Scope
- The unreachable 40% `should_inflict_wound()` threshold branch and `WOUND_THRESHOLD_RATIO` cleanup (owned by TCK-20260824-WOUND-THRESHOLD-DECISION)
- The wound-healing trigger decision (owned by TCK-20260824-WOUND-HEALING-DECISION)
- Wiring `speed_penalty` into `get_effective_stats` -- flag as an explicit follow-up decision, not silently included in this fix

## Acceptance Criteria
- [x] combat.py's `_get_wound_infliction()` constructs `WoundState` via `WoundService.create_wound()` instead of a flat penalty=5.0
- [x] Two wounds of different severity produce measurably different penalties through the live path, verified by a new test
- [x] `wound.max_hp_penalty` is non-zero for severe wounds and reduces effective max_hp
- [x] Test asserts live wound penalties scale with severity, not a pinned constant of 5.0
- [x] docs/mechanics/01_entity_anatomy.md, docs/mechanics/02_combat_laws.md, and COMB-072/073/102/103 are corrected to match the live-wired formula

## Related Tickets
- TCK-20260429-E3-MISSING-LOGIC
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260824-WOUND-HEALING-DECISION
- TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/02_combat_laws.md
- docs/mechanics/damage_formula_contract.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/combat.py
- src/engine/rpg_depth.py
- src/core/state.py
- src/engine/apply.py
- src/core/updates.py
- src/engine/patches.py

## Assumptions / Open Questions
- Recommended to land BEFORE TCK-20260824-WOUND-THRESHOLD-DECISION (C2) is finalized, since this wiring narrows C2's dead-code scope
- Whether speed_penalty should be wired into get_effective_stats in this ticket or as a separate follow-up is an open decision -- currently deferred as out of scope
- Must not accidentally swap in should_inflict_wound()'s 40% gating threshold -- only the penalty formula is in scope here, not the infliction threshold (C2's territory)

## Implementation Notes
`src/engine/combat.py::CombatResolutionSystem._get_wound_infliction()` (lines ~604-618) previously
constructed `WoundState` by hand with a hardcoded flat `atk_penalty=5.0, def_penalty=5.0` (and never
set `speed_penalty`/`max_hp_penalty`, leaving them at their dataclass defaults of `0.0`). It now
delegates entirely to `WoundService.create_wound(damage=int(damage), max_hp=defender.combat.max_hp,
tick=tick, wound_id=w_id)` (imported locally from `src.engine.rpg_depth`, matching the function's
existing local-import style), which computes `severity = min(1.0, damage/max_hp)` and derives
`atk_penalty=int(severity*3)`, `def_penalty=int(severity*2)`, `speed_penalty=int(severity*2)`,
`max_hp_penalty=int(severity*10)` — exactly the formula this ticket's scope specifies. The 25%
single-hit infliction threshold (`if damage > defender.combat.max_hp * 0.25 and alive:`) is
untouched — that gating logic is out of scope here (owned by `TCK-20260824-WOUND-THRESHOLD-DECISION`
for the separate, unreachable 40% `should_inflict_wound()` branch; this ticket's own inline 25%
check was left as-is since the ticket only asked to change the penalty *construction*, not the
infliction trigger). `WoundState.kind` selection also changed as an unavoidable side effect of fully
delegating to `WoundService.create_wound()`: it now derives from severity (CRUSH/SLASH/PIERCE
thresholds) instead of the old attacker-role-based `"SLASH" if attacker.identity.role ==
EntityRole.HERO else "CRUSH"` — this was not separately specified by the ticket but follows directly
from "construct via `WoundService.create_wound()`".

`wound.max_hp_penalty` is now non-zero for severe wounds and required no further wiring to reduce
effective max_hp: `src/engine/apply.py`'s `ApplyPath._apply_entity_update()` already marks
`stats_dirty=True` whenever `update.wound_update is not None` and recomputes derived stats via
`SkillScalingService.get_effective_stats(..., wounds=new_com.wounds, ...)`
(`src/engine/rpg_depth.py:381-417`), which already applies `wound_pen["max_hp_penalty"]` to
`base_stats["max_hp"]` (line 417) — that consumer path was already correct/live, only the producer
(`_get_wound_infliction`) was broken. Verified end-to-end: a severity-0.99 wound applied through
`ApplyPath._apply_entity_update` reduces `combat.max_hp` from its pre-wound value.

**Follow-up not included in this ticket (explicit per Out of Scope):** `speed_penalty` is correctly
computed and stored on the wound now, but `get_effective_stats()` does not read `speed_penalty` at
all — no `move_cost`/speed stat is reduced by wounds today. Wiring `speed_penalty` into
`get_effective_stats` is a real, separate follow-up decision (deferred here per the ticket's Out of
Scope), not silently included in this fix.

## Test Summary
Added two new tests to `tests/unit/combat/test_direct_combat_outcomes.py`, both exercising the real
combat resolution entry point (`CombatResolutionSystem.resolve_attack`), not
`WoundService.create_wound()` in isolation:
- `test_wound_penalties_scale_with_severity_through_live_combat_path` — two attacks (damage=40 vs
  damage=99 against max_hp=100, severities 0.4 and 0.99) produce wounds with measurably different
  `atk_penalty`/`def_penalty`/`speed_penalty`/`max_hp_penalty`, none pinned to the old flat `5.0`,
  each matching the `int(severity * N)` formula exactly.
- `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path` — a severe wound's
  `max_hp_penalty` is non-zero and, once the resulting `WoundUpdate` is run through
  `ApplyPath._apply_entity_update` (the authoritative apply path), `combat.max_hp` measurably drops.

Final independent Test-phase run (test-scoper agent, re-running rather than trusting this prior
claim): `tests/unit/combat/`, `tests/unit/core/test_rpg_depth.py`,
`tests/unit/core/test_entity_integrity.py`, `tests/unit/core/test_p1_semantic_hardening.py`,
`tests/unit/core/test_rpg_math.py`, `tests/unit/observability/test_event_extractor_vitals.py`,
`tests/integration/combat/`, `tests/integration/pipeline/test_combat_legality_matrix.py`,
`tests/integration/pipeline/test_combat_trust.py`, `tests/integration/optimization/test_apply_plan_parity.py`,
`tests/unit/domains/combat_engagement/`, `tests/integration/domains/combat_engagement/` —
262 passed, 0 failed. Structural test-scope-coverage backstop check: no gaps.

## Files Changed
- `src/engine/combat.py` — `_get_wound_infliction()` now delegates to `WoundService.create_wound()` (imported from `src/engine/rpg_depth.py`)
- `tests/unit/combat/test_direct_combat_outcomes.py` — 2 new tests (live-path severity scaling, max_hp_penalty apply-path reduction)
- `docs/mechanics/01_entity_anatomy.md`, `docs/mechanics/02_combat_laws.md` — corrected to describe the real severity-scaled formula, replacing the flat -5/-5 bug description
- `docs/parity_ledger/combat_movement.yaml` — COMB-072/073/102/103/104 updated (stale evidence + null test_path corrected to real citations + passing tests); new entry COMB-314 added for the live-path wiring fix itself

## Completion Summary
Wired the severity-scaled wound/scar penalty formula into the live combat path. `combat.py`'s
`CombatResolutionSystem._get_wound_infliction()` no longer hand-builds a `WoundState` with a flat
`atk_penalty=5.0, def_penalty=5.0` (and `speed_penalty`/`max_hp_penalty` implicitly stuck at 0.0);
it now delegates entirely to `WoundService.create_wound()` (`src/engine/rpg_depth.py`), which
computes `severity = min(1.0, damage/max_hp)` and derives `atk_penalty=int(severity*3)`,
`def_penalty=int(severity*2)`, `speed_penalty=int(severity*2)`, `max_hp_penalty=int(severity*10)`.
Verified end-to-end through the real combat resolution entry point
(`CombatResolutionSystem.resolve_attack`), not just `WoundService.create_wound()` in isolation: two
attacks of different severity (0.4 and 0.99) now produce measurably different penalties on every one
of the four stats, and a severe wound's non-zero `max_hp_penalty` measurably reduces an entity's
effective max_hp once the resulting `WoundUpdate` is run through `ApplyPath._apply_entity_update` —
`get_effective_stats()` already consumed `max_hp_penalty` correctly (`src/engine/rpg_depth.py:417`),
so only the broken producer needed fixing, not the consumer.

Docs corrected to match: `docs/mechanics/01_entity_anatomy.md` and `docs/mechanics/02_combat_laws.md`
no longer describe the flat -5/-5 bug; both now state the real severity-scaled formula.
`docs/parity_ledger/combat_movement.yaml` COMB-072/073/102/103/104 (previously P0 with stale
"exhaustive checklist audit" evidence and no `test_path`) now cite the real live-wired source and a
real passing test each; new entry COMB-314 documents the live-path wiring fix itself. COMB-290 (the
25% infliction-threshold entry, a distinct concern from the penalty formula) was deliberately left
untouched, per this ticket's explicit out-of-scope boundary.

Tests added: 2 new tests in `tests/unit/combat/test_direct_combat_outcomes.py`, both driving the
real `resolve_attack()` entry point end-to-end rather than re-testing `WoundService.create_wound()`
alone. Full independent scoped run (re-executed by the Test-phase agent, not just trusted from
Implement): 262 passed, 0 failed; structural test-scope-coverage backstop found no gaps.

**One known, explicitly out-of-scope gap remains, not silently included in this fix:**
`speed_penalty` is now correctly computed and stored on every wound, but `get_effective_stats()`
does not read `speed_penalty` at all — no `move_cost`/speed stat is reduced by wounds today. Wiring
`speed_penalty` into `get_effective_stats` is a real, separate follow-up decision, deferred per the
ticket's own Out of Scope section (not silently wired in as part of this fix). No follow-up ticket
exists yet for this specific gap as of this ticket's close; it should be picked up either as its own
follow-up or folded into `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, which depends on this ticket's
wiring and is best positioned to make that call.
