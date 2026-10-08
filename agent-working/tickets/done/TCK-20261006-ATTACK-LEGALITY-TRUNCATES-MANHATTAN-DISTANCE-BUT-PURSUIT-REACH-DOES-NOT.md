---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT
phase: done
date: 2026-10-06
tags: [combat, cognition]
---

# TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT

## Title
On fractional positions the attack legality check and the pursuit reach check disagree about the same Manhattan distance: legality truncates it with `int()` (1.72 becomes 1, in reach) and the pursuit reach test compares it as a float (1.72 > 1, not in reach).

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by `rpg-implementer` while tracing the held out-of-range attack loop (`TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`), filed on `rpg-feature-planning`'s ruling as its own ticket and **deliberately not fixed there**: fractional positions are a movement-model question and need their own discriminator.

Melee adjacency is orthogonal, Manhattan distance <= 1 (world rule MOV-07, owner decision under memo row 20; its docs PR was about to open when this was filed). Two call sites compute that distance differently:
1. `src/engine/legality.py:38-43` `LegalityServiceV2.get_manhattan_dist` returns `int(abs(dx) + abs(dy))`, so an attacker at `(93.34, 71.06)` and a target at `(94.0, 70.0)` (distance 1.72) is `1`, and `verify_attack_legality` accepts the melee attack. Used by the tactical pass (`tactical.py`, the legal-target filter) and by `execute_attack`.
2. `src/engine/candidate_selector.py:116-123` `MovementCandidateSelector._target_in_attack_reach` computes `abs(dx) + abs(dy)` as a float and returns `False` for `reach <= 1.5 and dist > 1`, so the same pair is NOT in reach and a pursuit move toward it does not complete.

Measured (read-only, seed 42, 2000 ticks, `crowded_frontier`, main `7f361ee73`): 5 of 9 tactical ATTACK decisions were made at a float distance above 1 (1.585 to 1.859); every one passed `verify_attack_legality` and every one executed successfully, so the truncation is currently what lets them strike. Whether the pursuit-completion side can hold a pursuer that legality would already let attack was **not measured**.

## Scope
1. Decide which distance is law for fractional positions (floor, round, or the float itself) and apply it at both call sites through one shared helper. A rules and movement-model question: ask the world-rules owner before implementing.
2. Re-measure the corpus (both worlds, seed 42, 2000 ticks, `audit_mode`, budget off, twice): ATTACK decisions at float distance above 1, pursuit completions that disagree with legality, and the deliberate-attack count.

## Out of Scope
- The orthogonal-adjacency ruling itself (MOV-07), the held-attack task clear, the same-tick overshoot guard.

## Acceptance Criteria
- [x] The distance rule for fractional positions is ruled and recorded.
- [x] Both call sites use one helper; a constructed fractional pair gives the same answer from legality and from pursuit reach.
- [x] The corpus before/after is reported, including zeros, with the re-baseline disclosed.

## Related Tickets
- `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED` — where it was found.
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — introduced `_target_in_attack_reach`.

## Related Docs
- `docs/mechanics/02_combat_laws.md` section 7 (legality), `docs/combat/combat_movement_overhaul_spec.md` (melee adjacency).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED/probes/` (`atk_origin.py`, `atk_origin_dbg.py`).

## Related Code Areas
- `src/engine/legality.py` (`get_manhattan_dist`, `verify_attack_legality`)
- `src/engine/candidate_selector.py` (`_target_in_attack_reach`, `tracked_move_complete`)

## Assumptions / Open Questions
- Resolved: fractional positions are a leak from one path, the flow-field step (9 of 9 and 13 of 13 births), not an intended sub-tile model. Decision 25 (owner delegation, 2026-10-07; memo row 25) amends MOV-07: positions are whole tiles. MOV-07's evidence line stays CONFLICTING until a later designer batch flips it.

## Implementation Notes
First commit: the designer's ruling patch. Then: `navigation.py` flow step is a one-tile step along the vector's dominant axis (tie takes y, as the local step); `legality.py` `get_manhattan_dist` is the distance between the tiles the positions stand on (no truncated sum); `candidate_selector._target_in_attack_reach` calls it. Parity: Bible 02 section 7 bullet, ledger COMB-337 and COMB-333's support boundary, divergence 2.83 (Bug Fix). Probes in the stored artifacts. Re-baseline disclosed in 2.83: walks to the town centre follow a Manhattan path, so trajectories diverge from main; `grade_anchors.json` not re-measured.

## Test Summary
New `tests/unit/engine/test_attack_reach_distance.py` (7 cases) and three new flow tests in `tests/unit/movement/test_flow_field_navigation.py` (one existing test that pinned the leak was updated). Scoped run: `tests/unit/{combat,engine,movement,actions,core,tools,systems}` 1439 passed, 1 skipped. Corpus (seed 42, 2000 ticks, `audit_mode`, budget off, governor pinned to NORMAL, main `753f98ea9` vs branch, `crowded_frontier` / `frontier_living_world`): entities between tiles at any tick 1 / 3 to 0 / 0; reach versus legality disagreements 4 / 110 to 0 / 0; ATTACK decisions 46 / 49 to 45 / 109; dead or removed 40 / 50 to 40 / 50; EAT 3 / 43 to 7 / 36; REST 0 / 0 to 2 / 15. Determinism: the after arm run twice per world, identical digests.

## Files Changed
`src/systems/world_systems/navigation.py`, `src/engine/legality.py`, `src/engine/candidate_selector.py`, `tests/unit/engine/test_attack_reach_distance.py`, `tests/unit/movement/test_flow_field_navigation.py`, `docs/mechanics/02_combat_laws.md`, `docs/parity_ledger/combat_movement.yaml`, `docs/guidelines/intentional_divergences.md`, the Decision 25 patch (`owner_decision_memo.md`, `movement-navigation.md`), `docs/REGISTRY.yaml`, stored artifacts with probes.

## Completion Summary
Positions are whole tiles. The one source of fractional positions, the long-distance flow-field step, is now a one-tile axis step; attack legality and pursuit reach share one whole-tile distance. 0 entities between tiles and 0 reach disagreements on both corpus worlds. Re-baselined and disclosed (divergence 2.83).
