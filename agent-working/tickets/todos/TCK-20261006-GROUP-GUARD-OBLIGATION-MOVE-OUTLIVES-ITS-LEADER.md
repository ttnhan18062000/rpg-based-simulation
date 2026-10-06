---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER
phase: open
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER

## Title
A group hireling's `CONTRACT_OBLIGATION_GUARD` move checks its leader's liveness only when the guard is
decided, and nothing ends the move afterwards, so it keeps guarding a dead leader

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by `rpg-implementer` while measuring gate 4
(`TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`), and deliberately
left out of it, because guarding has its own lifecycle and gate 4's fix covers combat-positioning moves only.

**Path (traced, not inferred):** `src/engine/tactical.py:381-399`, "4.1 Role-Based Obligation (Phase 7)". A group
hireling with role `VANGUARD` or `PROTECTOR` guards its group's leader while the leader is interacting. The
leader's liveness (`leader.combat.alive`) is checked **at decision time only**; nothing ends the move afterwards.

**It is NOT the social-contract path.** No `SocialContractScorer` is involved, so it does not fold into
`TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT`. The name
`CONTRACT_OBLIGATION_GUARD` is misleading here.

**Why P3:** measured as a live mover guarding a dead leader for only **16 ticks** before the mover itself died, in
two worlds. Real, but brief and rare.

## Scope
1. Decide the guard's intended end: leader dead, leader no longer interacting, or the group dissolved.
2. End the move on that condition, through the same completion mechanism gate 4 uses
   (`pursuit_completion_update`), rather than a parallel termination path. Keep guarding's own lifecycle otherwise
   intact, per gate 4's scoping.
3. Disabling-control test: a guard whose leader dies ends its move.

## Out of Scope
- Combat-positioning moves (gate 4). Social contracts (ticket (c)).

## Acceptance Criteria
- [ ] End condition decided and recorded.
- [ ] A guard of a dead leader ends its move; disabling-control result recorded.
- [ ] Measured before and after, as values.

## Related Tickets
- `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION` (gate 4).
- `TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE`.

## Related Docs
- `docs/engine/` tactical contract.

## Related Stored Artifacts
- Gate 4's `target_move_lifetimes.py` probe.

## Related Code Areas
- `src/engine/tactical.py:381-399`.

## Assumptions / Open Questions
- **Lane.** Lane A, after gate 4. Needs the `tactical.py` hold, which Lane A already holds.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
