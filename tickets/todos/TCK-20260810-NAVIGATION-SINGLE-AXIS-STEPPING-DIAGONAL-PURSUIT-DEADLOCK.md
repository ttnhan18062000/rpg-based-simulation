---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK
phase: open
date: 2026-08-10
tags: [combat, engine]
---

# TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK

## Title
`NavigationSystem.get_next_step()`'s single-axis-priority stepping (never moves diagonally) can
trap two mutually-pursuing entities in a stable, non-converging orbit around each other instead
of closing to melee range

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Disclosed finding from `TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS`
(DONE, same session): after fixing pursuit to correctly live-retarget toward a chased entity's
CURRENT position at all 4 real call sites, the specific mutually-pursuing pair that ticket traced
(`dungeon_crawl_seed42_2000t`, entities 25 and 12) stopped freezing outright, but still never
converges to melee range (Manhattan distance ≤1). Instead, both entities perpetually swap which
diagonal corner they occupy relative to each other, tick after tick, staying at exactly Manhattan
distance 2.0 indefinitely.

Root cause (not yet confirmed with a full trace, only observed): `NavigationSystem.get_next_step()`
(`src/systems/world_systems/navigation.py:99-103`) does axis-priority single-step movement —
`if abs(dx) > abs(dy): move along X only; else: move along Y only` — never both axes in the same
tick. When two entities are on a pure diagonal offset from each other (`abs(dx) == abs(dy)`, e.g.
`dx=-1, dy=-1`) and BOTH are live-retargeting toward each other's current position every tick
(now correctly happening, post the sibling ticket's own fix), each entity's own single-axis step
can effectively cause them to orbit rather than close the gap, since the "other" entity is also
moving in response to the SAME live position it's chasing.

## Scope
1. **Investigate** (mandatory before Plan): capture a full per-tick position trace of the
   specific pair (or an equivalent reproduction) to confirm the exact stepping sequence that
   produces the orbit — is it deterministic and universal for any pure-diagonal offset, or
   specific to this pair's own starting geometry? Check whether `get_next_step`'s own "Arrived?"
   `dist < 0.1` check or something else in the stepping sequence is the load-bearing mechanism.
2. Determine real corpus-wide prevalence: how many real pursuit pairs in `dungeon_crawl`/
   `urban_political` (and ideally other corpus worlds — see the user's own related question
   about combat-metric coverage outside these two) hit a pure-diagonal offset relationship
   during pursuit, vs. how many converge normally via non-diagonal approach angles.
3. If confirmed real and non-trivial in prevalence: scope a minimal fix — likely either (a)
   allowing `get_next_step` to move both axes when the offset is diagonal (true 8-directional
   stepping), or (b) breaking the specific orbit pattern via existing anti-stalemate machinery
   (`stale_ticks`/`STALEMATE_BREAK`, which currently only fires on exact position-repeat, not
   this kind of oscillating-but-never-repeating orbit).
4. If real corpus prevalence turns out to be low/rare: document and leave as a known, disclosed,
   low-priority limitation rather than force a change to core movement stepping logic.

## Out of Scope
- Any other movement-mode-specific bug not tied to this exact diagonal-offset condition.
- The already-fixed live-retargeting mechanism itself
  (`TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS`).
- Building true A* diagonal pathfinding for long-range navigation — this ticket is scoped to the
  local, single-step `get_next_step` function's own pursuit-adjacent behavior only.

## Acceptance Criteria
- [ ] investigation.md documents a confirmed, real per-tick trace of the orbit mechanism
- [ ] Real corpus-wide prevalence is measured (not assumed) across at least `dungeon_crawl` and
      `urban_political`, and ideally a broader sample of corpus worlds
- [ ] A concrete recommendation is produced (fix vs. document-and-defer), with reasoning
- [ ] If a fix lands: real corpus re-verification shows the specific traced pair (or an
      equivalent) converging, with no regression to existing movement-mode tests (none currently
      exist for `get_next_step` directly — confirmed via `grep -rln "get_next_step" tests/`
      returning zero results, so a new fix here would need its own first direct test coverage)

## Related Tickets
- TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS (DONE, same session — the
  ticket whose own Verify phase found and disclosed this issue)
- TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE (COMB-304 — the original live-retargeting fix this
  behavior is downstream of)

## Related Docs
- `docs/engine/contracts/tactical_contract.md` §3 (Engagement & Pursuit Rules)
- `docs/compliance/checklist.md` §7 (A* pathfinding details — COMB-167 through COMB-172, none of
  which currently cover diagonal-offset pursuit convergence specifically)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS/investigation.md`
  (the trace that first surfaced this, pre-dating this ticket's own dedicated investigation)

## Related Code Areas
- `src/systems/world_systems/navigation.py` (`NavigationSystem.get_next_step()`, lines ~78-103)
- `src/engine/movement.py` (`MovementSystem.resolve_move()`, the caller)
- `src/engine/tactical.py` (Anti-Stalemate `STALEMATE_BREAK` logic, lines ~406-433 — may already
  be a viable escape hatch if the orbit's own position-repeat pattern is detectable)

## Assumptions / Open Questions
- Whether this is common enough in the real corpus to be worth fixing, or rare enough (specific
  to certain starting-geometry pursuit pairs) to just document — not assumed either way; the
  first real Investigate step here is to measure prevalence before deciding.

## Implementation Notes
(filled during Investigate/Implement)

## Test Summary
(filled during Test)

## Files Changed
(filled during Finalize)

## Completion Summary
(filled during Finalize)
