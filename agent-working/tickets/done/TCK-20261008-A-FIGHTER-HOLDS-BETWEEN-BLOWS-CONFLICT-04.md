---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04
phase: done
date: 2026-10-08
tags: [combat]
---

# TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04

## Title
A fighter beside an engaged hostile holds its tile between blows instead of stepping, and the stalemate breaker no longer fires mid-melee (world rule CONFLICT-04).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
World rule CONFLICT-04, "A fighter stands its ground between blows; leaving an engagement is a decision, and it has a cost." The owner confirmed it directly on 2026-10-08, via rpg-designer. It is memo row 28 in `docs/world_rules/capability-progression/conflict-combat.md`, on the designer's branch `conflict-04-hold-between-blows` (7c9ffc29f).

Evidence comes from Lane A's opportunity-attack trace (pinned, seeds 42-46, 3 worlds, stored with TCK-20261007-A-WALKER-...-PER-STEP):
- 83 to 98 percent of opportunity-attack swings land on a victim that is adjacent to the attacker.
- `src/engine/tactical.py` 739-829 allows ATTACK/SKILL only when `is_attack_legal`, which needs readiness 100 for a normal attack. Otherwise the subject PURSUES, even when it is already adjacent. That step provokes an opportunity attack.
- `tactical.py` 495-524 sends the subject to a STALEMATE_BREAK WANDER when `stale_ticks > 10`, before any attack branch, even when it is adjacent. The ATTACK/SKILL payloads (about 772 and 788) carry `stale_ticks + 1` on every swing. Tactical contract §5's trigger is "without a target change or outcome", so a swing is an outcome and should reset the counter.

## Scope
1. **Hold between blows (Intentional Gameplay Change).** A subject adjacent to a perceived, engaged hostile whose attack is not legal this tick (readiness under 100) HOLDS: it does not step, so it provokes no opportunity attack. PURSUE applies only when the target is not adjacent. There is no non-provoking reposition. Leaving the engagement happens only through an existing decision: AGENCY-07 flight, PANIC_RETREAT, a declared ability such as EVASIVE retreat, or a goal that genuinely outranks the fight. SURV-07 needs stay below a present threat.
2. **Hold is a typed action**: a hold or guard task, not an empty step or a missing update. Reuse an existing TaskType or hold action if one fits (the chokepoint hold at about tactical.py 663-676 is a candidate). Ask rpg-planner before adding a new field or enum value in `src/core/state.py` or `src/engine/apply.py` (perf #415).
3. **Target preference:** when picking a target, prefer an adjacent engaged hostile.
4. **Suppress STALEMATE_BREAK** while a perceived hostile is adjacent and the subject is fighting it.
5. **Stall counter (Bug Fix):** a successful ATTACK/SKILL swing resets `stale_ticks` (an outcome, per tactical contract §5) instead of adding 1. Pursuit and position-repeat bookkeeping are unchanged.
6. **Docs, same PR:**
   - `docs/mechanics/02_combat_laws.md` §7: add the "between blows the fighter holds" sentence.
   - `docs/engine/contracts/tactical_contract.md` §5: the suppression, and the swing-resets rule.
   - `docs/guidelines/intentional_divergences.md`: two entries, Intentional Gameplay Change (hold) and Bug Fix (stall counter), at the next free numbers at rebase.
   - `docs/parity_ledger/combat_movement.yaml`: new or updated entries with test_path.

## Out of Scope
- Subjects that move with no move task (the largest opportunity-attack class: task ENTITY_ACT, leftover navigation mode, no tactical decision that tick). That is a separate engine-defect ticket, scoped after Lane A's read-only trace.
- The held-move interrupt (WIP 7f2455353, parked, not built on).
- The opportunity-attack rule itself (COMB-009) and the readiness gate value.
- Flipping the CONFLICT-04 evidence: rpg-designer does that after this merges.

## Acceptance Criteria
- [x] Scenario CP-S18 (kernel, with control arm) in tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py: a non-cautious fighter with readiness under 100, adjacent to an engaged hostile, holds and takes no opportunity attack until it chooses to leave.
- [x] Scenario CP-S19 (kernel, with control arm) in tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py: a long exchange of blows never trips STALEMATE_BREAK while the pair stays adjacent.
- [x] Unit: a swing resets `stale_ticks`; a non-adjacent target still produces PURSUE; flight and panic retreat still leave (and pay the opportunity attack).
- [x] Pinned 5-seed report, seeds 42-46 x 3 worlds, mean (SD), before and after: opportunity-attack hits split into decided, held-move and neither classes; DEFEAT deaths; total deaths; alive at t=1000 and t=1100. Two-run determinism. Report it, don't tune. A small total effect is expected while the "neither" defect stands.
- [x] Gates: mypy, ratchet, lint-imports (17 kept, 0 broken), mechanism completeness pin.

## Related Tickets
- TCK-20261008-A-READINESS-REJECTED-QUEUED-ACTION-WRITES-A-CAPABILITY-BLOCKER-THAT-FEEDS-RESOLVE-BLOCKER (absorbed into this ticket by rpg-planner's ruling; divergence 2.88, COMB-341)
- TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP (the trace's source; to be re-scoped to the movement-with-no-move-task defect)
- Attack-distance (MOV-07 whole tiles, divergence 2.83). This ticket stacks on it, because the provoke check reads reach from whole tiles.
- AGENCY-07 (#398), SURV-07 (#414).
- Adjacent ATTACK holders already hold after #429 (the scheduler's non-brain readiness gate skips them and nothing moves them). This ticket covers the BRAIN path: PURSUE when adjacent, and STALEMATE_BREAK.

## Related Docs
- `docs/world_rules/capability-progression/conflict-combat.md` (CONFLICT-04, row 28)
- `docs/mechanics/02_combat_laws.md` §7, `docs/engine/contracts/tactical_contract.md` §5

## Related Stored Artifacts
- Lane A's oa_table.md and oa_trace_summary.txt (staging artifacts of the OA ticket)

## Related Code Areas
- `src/engine/tactical.py` (495-524 stalemate, 739-829 attack/pursue), `src/engine/tactical_threat.py`, `get_engaged_hostiles`, `LegalityServiceV2.verify_attack_legality`

## Assumptions / Open Questions
- An existing hold or guard task type can express the hold without touching state.py or apply.py. If not, ask rpg-planner first.

## Implementation Notes
Hold shape (accepted by rpg-planner): a queued ATTACK task, payload reason `HOLD_BETWEEN_BLOWS`, emitted when the target is adjacent, only readiness is missing (legality passes with the readiness bypass). The chokepoint ENTITY_ACT `HOLD` was not reused: ActionRouter has no HOLD handler, so it ends as UNSUPPORTED_ACTION each time (existing bug, out of scope; recorded in investigation.md and routed to rpg-planner). No state.py or apply.py change.
The `stale_ticks` reset happens when ATTACK/SKILL is emitted, not when a swing lands; this is the reading of tactical contract section 5's "outcome".
Trade-off: while holding, the entity is a non-brain item and cannot decide to flee until the swing or a release (OUT_OF_RANGE, TARGET_INCAPACITATED).

## Test Summary
Unit, combat, engine, actions and mechanic_scenarios sweeps pass (670 before the final merge of main; 207 re-run after it). Kernel scenarios CP-S18 and CP-S19 (each with a control arm; both mains fail on `main`) are in tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py. tests/unit/actions/test_readiness_wait_writes_no_blocker.py covers divergence 2.88. Mechanism completeness pin updated (312 files, 232 unbound). Ratchet, mypy gate and lint-imports (17 kept) green. Pinned 5x3 reports in divergences 2.86 and 2.88: effect small, deaths inside 1 SD, no deaths after a low-HP hold, blocker episodes 0 after the fix, two-run digests equal.

## Files Changed
src/engine/tactical.py, src/engine/tactical_hold.py (new), src/engine/pipeline_phases/actions.py, registries/mechanisms.yaml, tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py, tests/unit/actions/test_readiness_wait_writes_no_blocker.py, tests/unit/combat/{test_anti_stalemate,test_capability_driven_targeting,test_tactical_destinations}.py, tests/unit/tools/test_mechanism_registry_completeness_check.py, docs/mechanics/02_combat_laws.md, docs/engine/contracts/tactical_contract.md, docs/guidelines/intentional_divergences.md (2.86, 2.87, 2.88), docs/parity_ledger/combat_movement.yaml (COMB-339, COMB-340, COMB-341).

## Completion Summary
A fighter beside an engaged hostile holds a queued swing between blows; adjacent hostiles rank first; STALEMATE_BREAK skips an adjacent target; ATTACK/SKILL emission resets stale_ticks. Chokepoint HOLD router gap recorded for rpg-planner. Readiness-blocker follow-up absorbed (2.88).
