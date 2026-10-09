---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-A-SUBJECT-NOTICES-AN-UNENGAGED-HOSTILE-COMING-ADJACENT-AND-DECIDES-DECISION-32
phase: done
date: 2026-10-08
tags: [combat]
---

# TCK-20261008-A-SUBJECT-NOTICES-AN-UNENGAGED-HOSTILE-COMING-ADJACENT-AND-DECIDES-DECISION-32

## Title
A subject notices when a perceived hostile it is not fighting comes adjacent and decides right then (owner decision 32, CONFLICT-04 scope).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision 32 (designer commit 6eba4582b): an unengaged perceived hostile coming adjacent prompts a fresh decision then. Release-to-brain alone could not meet it (an idle task runs the brain on its stagger tick, up to 10 ticks later, and 80 percent of episodes end within 3 ticks), so the scheduler wakes the brain (approved by rpg-planner as an exception to the scheduler no-touch rule; perf informed).

## Scope
Scheduler wake (`ADJACENCY_WAKE_COOLDOWN` 2, stateless, LOD bypass), the posture-following decision (`notice_unengaged_hostile`), `KEEP_WALKING` released on arrival, `AVOID_HOSTILE` a decided flight; unit tests, kernel scenario with control arm, bounded-decision invariant; divergence 2.95, parity COMB-343, Bible 02 section 7, tactical contract, mechanism note; pinned 5x3 at 1500 and 5000 ticks.

## Out of Scope
- Any movement-layer freeze (rejected by the decision); a `watch` semantic change (the designer decides); content for `ignore`.

## Acceptance Criteria
- [x] Every two-tick adjacency episode with an unengaged perceived hostile is followed by a brain decision within the bound (2 ticks): the pinned-run invariant counts 0 violations.
- [x] Pinned 5x3 with OA hits by class, deaths, alive, brain decisions, resolve_move, two-run digests (divergence 2.95).
- [x] cProfile and the LOD-bypass count are stated.

## Related Tickets
- TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04 (#439); the free-hit batch (#446); TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02 (the arms are attributed).

## Related Docs
- `docs/world_rules/capability-progression/conflict-combat.md` (CONFLICT-04, decision 32); `docs/mechanics/02_combat_laws.md` section 7; `docs/engine/contracts/tactical_contract.md`.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-A-SUBJECT-NOTICES-AN-UNENGAGED-HOSTILE-COMING-ADJACENT-AND-DECIDES-DECISION-32/` (investigation.md, probes/).

## Related Code Areas
- `src/engine/scheduler.py`, `src/engine/candidate_selector.py`, `src/engine/tactical_hold.py`, `src/engine/tactical.py`.

## Assumptions / Open Questions
- `ignore` never occurs (a later ticket makes it reachable through combat engagement); `watch` is a typed HOLD wait (designer ruling). The idle residual of the free-hit batch (an idle task blocked beside an engaged hostile for up to 19 ticks) is not re-measured separately: blocked entity-ticks are 0 in every arm of this batch's measurement.

## Implementation Notes
See the investigation.

## Test Summary
`tests/unit/engine/test_notice_unengaged_hostile.py` (15), `tests/mechanic_scenarios/test_decision32_notice_and_decide.py` (3); ratchet OK, mypy clean, import-linter 17 kept, 0 broken.

## Files Changed
tests/mechanic_scenarios/test_conflict04_movement_layer.py (the #446 invariant now uses the movement rule's own decided-flight exemption, `MovementCandidateSelector.is_decided_flight`, instead of being stricter than the rule; a unit case covers a held PANIC_RETREAT);
src/engine/scheduler.py, candidate_selector.py, tactical_hold.py, tactical.py; tests as above; docs, registries/mechanisms.yaml, parity COMB-343.

## Completion Summary
Opportunity-attack hits fall 33 to 67 percent at 1500 ticks (post-WATCH); every adjacency gets a decision; the long-run effect is a delay.
