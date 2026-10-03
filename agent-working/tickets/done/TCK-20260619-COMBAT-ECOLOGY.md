---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260619-COMBAT-ECOLOGY
phase: done
date: 2026-06-20
tags: [combat, nemesis, grudge, rivalry, combat-ecology, verification]
---

# TCK-20260619-COMBAT-ECOLOGY

## Title
Combat Ecology Extension — Nemesis/Grudge Depth Verification and Extension

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Persistent grudges and tactical-avoidance of known foes already exist. Verified scope boundary. Extended with `combat_loss_counts` and `fear_avoidance` posture.

## Scope
- Investigated grudge/nemesis implementation depth
- Verified scope is run-only (cross-episode BLOCKED by Epic 3.2)
- Added `combat_loss_counts: Dict[int, int]` to `SocialComponent`
- Emit `combat_loss_delta` from combat on kill
- Fear avoidance posture when loss count >= 3

## Out of Scope
- Cross-episode persistence (requires Epic 3.2 CampaignState, not done)
- Full nemesis system with named narratives

## Acceptance Criteria
- [x] Investigation finding documented: grudge scope is run-only
- [x] `fear_avoidance` generated when entity loses to same opponent >= 3 times (AVOID posture forced)

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite for cross-episode, BLOCKED)

## Related Docs
- `docs/parity_ledger/combat_movement.yaml` (COMB-291, COMB-292 added)
- `staging_artifacts/TCK-20260619-COMBAT-ECOLOGY/investigation.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-COMBAT-ECOLOGY/`

## Related Code Areas
- `src/core/models/social.py` — added `combat_loss_counts`
- `src/core/updates.py` — added `combat_loss_delta`
- `src/engine/combat.py` — emit `combat_loss_delta` on kill
- `src/systems/social_systems/relationships.py` — apply `combat_loss_delta`
- `src/core/builder.py` — carry `combat_loss_counts`
- `src/core/state.py` — serialize `combat_loss_counts`
- `src/domains/combat_engagement/service.py` — fear_avoidance short-circuit at >= 3 losses

## Assumptions / Open Questions
- Cross-episode grudge persistence is clearly BLOCKED until Epic 3.2.

## Implementation Notes
Investigation findings:
1. Grudge accumulates from combat (`damage/max_hp` ratio) in `combat.py::resolve_attack` — already works
2. Nemesis promotion at grudge >= 3.0 via `memory.py::check_nemesis_promotion` — exists
3. Grudge is run-scoped only (SocialComponent lives on EntityState → AuthoritativeState)
4. No per-opponent discrete loss counter existed — grudge is float ratio, not integer count
5. No `fear_avoidance` behavior existed

Added `combat_loss_counts: Dict[int, int]` (discrete count, separate from float grudge) and wired `combat_loss_delta` from kill events through `SocialUpdate` → `RelationshipService`. The fear_avoidance short-circuit in `service.py` forces `CombatPosture.AVOID` when the loss count reaches 3.

## Test Summary
- `tests/unit/combat/test_combat_ecology.py` — 4 tests, all pass
  - `test_grudge_scope_is_defined` — verifies all grudge fields exist; documents run-only scope
  - `test_combat_loss_increments_counter` — SocialUpdate.combat_loss_delta correctly applies
  - `test_fear_avoidance_posture_at_loss_threshold` — loss_count=3 forces AVOID posture
  - `test_no_fear_avoidance_below_threshold` — loss_count=2 does not force AVOID

## Files Changed
- `src/core/models/social.py` — added `combat_loss_counts: Dict[int, int]`
- `src/core/updates.py` — added `combat_loss_delta`, updated `is_noop()` and `merge()`
- `src/engine/combat.py` — emit `combat_loss_delta={attacker.id: 1}` when defender killed
- `src/systems/social_systems/relationships.py` — apply `combat_loss_delta` in `process_update()`
- `src/core/builder.py` — added `combat_loss_counts` to `.social()` method
- `src/core/state.py` — serialize `combat_loss_counts` in debug summary
- `src/domains/combat_engagement/service.py` — fear_avoidance short-circuit at loss_count >= 3
- `docs/parity_ledger/combat_movement.yaml` — appended COMB-291 and COMB-292
- `tests/unit/combat/test_combat_ecology.py` — NEW: 4 tests

## Completion Summary
Grudge scope verified as run-only (cross-episode blocked by Epic 3.2). Added `combat_loss_counts` integer counter and wired it through the full update pipeline. Fear avoidance forces AVOID posture when the same opponent has killed the entity 3+ times. 4 new tests; parity ledger updated with COMB-291 and COMB-292.
