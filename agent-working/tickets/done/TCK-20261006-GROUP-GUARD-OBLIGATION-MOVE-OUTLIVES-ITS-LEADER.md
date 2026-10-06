---
status: historical
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER
phase: done
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER

## Title
A group hireling's `CONTRACT_OBLIGATION_GUARD` move checks its leader's liveness only when the guard is
decided, and nothing ends the move afterwards, so it keeps guarding a dead leader

## Status
DONE

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
- [x] End condition decided and recorded (investigation section 3): the move ends when its obligation is gone. Leader dead, inactive or gone ends it; so does the mover leaving the leader's group (`CONTRACT_OBLIGATION_GUARD`). A leader merely pausing does not (INTERACT runs have gaps of up to 11 ticks), and reach does not.
- [x] A guard of a dead leader ends its move; disabling-control result recorded (guard kinds untracked fails exactly 5 tests; group condition off fails exactly 1).
- [~] Measured before and after, as values: legacy arm 1 guard move in `urban_political` (held 1004 ticks, **mover already dead**, 0 live-mover ticks with a dead leader, 3 with the group gone), after arm 0 guard moves in all 8 runs. **No per-move before and after exists**: the one legacy instance does not recur once entities are freed, and the corpus has no live-mover instance. Stated, not hidden; correctness rests on construction plus the unit tests.

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
`MovementCandidateSelector.tracked_move_complete` (gate 4's helper) now tracks two more kinds keyed on (`GUARD`, reason): `CONTRACT_OBLIGATION_GUARD` and `GUARDING_ALLY`. `_combat_positioning_kind` became `_tracked_move_kind` and the reach arithmetic moved to `_target_in_attack_reach`, so the per-function complexity stays under the project ceiling. No parallel termination path: both dispatchers already call the helper and apply `tracked_move_completion_update`.

Scope: `GUARDING_ALLY` was not in the ticket's text. It has the same structure and the same one-line dead-target condition, so it is included for that end only; it has 0 corpus moves and is covered by a constructed test.

The handover note's "16 live ticks in two worlds" is **not reproduced** by the probe (0 live-mover ticks with a dead leader) and is not used as evidence. Arriving does not end a move (the movement phase just stops moving), which is what makes the defect structural. Measurements were taken with the cwd set to this worktree; `src/core/registries.py` seeds content from the cwd-relative `data/content`, and a first attempt from another worktree crashed with `KeyError: stone_outcrop` and was discarded.

## Test Summary
`tests/unit/engine/test_pursuit_completion.py` 29 passed (8 new, 2 updated: the gate-4 pins that said guard moves are untouched); `tests/unit/engine` plus the two mechanism-registry checks 330 passed, 1 skipped. Code-health gates, reproduced in a scratch venv at the `uv.lock` versions (they cannot run in the project venv): `codebase.health check` first failed with 1 worse (`LocalSequentialExecutor.execute` 140 > ceiling 138, from gate 4's comment; fixed by trimming it), then **OK: 0 new, 0 worse**; `codebase.structure.packages validate` 0 problems; the mypy-baseline filter shows 10 `Returning Any` lines, none in a file this batch changed. CI is still the first run in the real environment. `ruff` via `uvx` with the project config: no findings on any line changed in `candidate_selector.py`.

## Files Changed
`src/engine/candidate_selector.py`, `tests/unit/engine/test_pursuit_completion.py`, `docs/engine/contracts/tactical_contract.md`, `docs/engine/kernel.md`, `docs/guidelines/intentional_divergences.md` (2.70 wording, new 2.71), `docs/parity_ledger/combat_movement.yaml` (COMB-331 wording, new COMB-332). Also corrected the previous ticket's probe script (`cd` and path) and added a reproduction note to its investigation.

## Completion Summary
A group guard move now ends when its leader (or ally) is dead, inactive or gone, and a guard obligation also ends when the mover leaves the leader's group. Known gaps: the live harm was not observed in the corpus (the one legacy instance had a dead mover) so no per-move before and after exists; whether a leader that stops interacting should also end the obligation is left open on measured evidence (no harm observed, flapping risk); the gates ran only in a scratch venv, so CI is the first real run.
