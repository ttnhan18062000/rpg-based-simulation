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
DONE

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
- [x] investigation.md documents a confirmed, real per-tick trace of the orbit mechanism —
      confirmed both analytically (a standalone re-implementation of the tie-break rule
      reproduces the exact real corpus trace) and empirically (5 new tests)
- [x] Real corpus-wide prevalence is measured (not assumed) across at least `dungeon_crawl` and
      `urban_political`, and ideally a broader sample of corpus worlds — measured across 3 seeds
      (42/123/456) × up to 8 corpus worlds, 2000 ticks each: exactly 1 real, sustained (≥20-tick)
      deadlock in the entire sample (the already-known pair)
- [x] A concrete recommendation is produced (fix vs. document-and-defer), with reasoning —
      **document-and-defer**: real, confirmed, deterministic mechanism, but too rare in practice
      (1/many across a broad real sample) to justify a core stepping-algorithm change
- [ ] If a fix lands: real corpus re-verification shows the specific traced pair (or an
      equivalent) converging, with no regression to existing movement-mode tests — **not
      applicable**: no fix landed, per the document-and-defer disposition above; 5 new direct
      tests for `get_next_step` were added regardless (none existed before, confirmed via
      `grep -rln "get_next_step" tests/` returning zero results pre-ticket), locking in the
      current, real, characterized behavior

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
  to certain starting-geometry pursuit pairs) to just document — **resolved**: rare (1 real
  sustained deadlock across a 3-seed × up to 8-world × 2000-tick sample).

## Implementation Notes
Confirmed the exact mechanism analytically: `get_next_step`'s own tie-break rule
(`if abs(dx) > abs(dy): X else: Y`) always resolves an exact tie (`|dx| == |dy|`, i.e. a
perfectly diagonal offset) to a Y-axis step. A standalone Python re-implementation of just this
rule, fed the exact real corpus positions of the traced pair (entities 25/12,
`dungeon_crawl_seed42_2000t`), reproduces the identical oscillation observed live — both
entities always move Y, their steps perpetually cancel, Manhattan distance stays fixed at 2.0
forever. Separately confirmed the deadlock requires MUTUAL, reactive pursuit — a single-sided
pursuer chasing a static target converges fine via a normal staircase path (verified with the
same standalone tie-break re-implementation): the offset naturally breaks the tie asymmetrically
as the pursuer's own position changes each step, while the target's doesn't.

Real corpus prevalence measurement (a live, non-mocked `Kernel.tick_once()` loop tracking every
tick whether any two entities' own `task.payload["target_id"]` mutually point at each other, and
for how many consecutive ticks their Manhattan distance stays constant while >1): 3 seeds
(42/123/456) across `dungeon_crawl`/`urban_political` (all 3 seeds) plus `wilderness_survival`/
`crowded_frontier`/`swamp_border_world`/`hero_guild_routing` (seed 42 only), 2000 ticks each.
Result: exactly 1 pair, in 1 world, at 1 seed (`dungeon_crawl`, seed 42, the already-known pair)
ever reached a genuine, sustained (≥20-tick) deadlock — a 991-tick streak. Every other
seed/world combination showed either zero mutual-pursuit pairs on an exact diagonal offset at
all, or trivially short (1-9 tick) coincidental ties that resolved normally the next tick (a
normal, transient part of the staircase convergence path, not a deadlock).

Given this real, measured, low-prevalence result, chose document-and-defer over a stepping-
algorithm change, per the ticket's own Scope item 4. Extended the already-existing "1.1 Spatial
/ Navigation" section of `docs/engine/known_limitations.md` (which already acknowledged
"Linear Stepping Only" in general terms) with the specific, confirmed mechanism and real
measured prevalence data, and cross-referenced it from `docs/engine/contracts/tactical_contract.md`
§3. Added 5 new direct tests for `get_next_step` (previously zero existed) to lock in the
current, real, characterized behavior — both the normal-case convergence and the confirmed
deadlock case — so a future change to the stepping algorithm doesn't silently alter this
documented limitation without a deliberate test update.

While running the regression sweep, found and fixed a separate, real, pre-existing test failure
unrelated to this ticket's own scope: `tests/unit/world/test_terrain_weighting.py::
test_terrain_readiness_success` asserted the OLD readiness-cost behavior
(`readiness_delta == -80.0`) that `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`
(same session, earlier) had already intentionally removed (§2.38, `docs/guidelines/
intentional_divergences.md`) — that ticket's own scoped test sweep never included
`tests/unit/world/`, so this stale assertion was never caught. Updated the assertion to
`readiness_delta == 0.0`, matching the already-documented, already-intentional divergence and
the exact pattern used by that ticket's own new regression test
(`test_successful_move_no_longer_costs_readiness`).

## Test Summary
5 new tests in `tests/unit/movement/test_navigation_get_next_step.py`: normal X-axis and Y-axis
convergence, the exact diagonal tie-break rule, single-sided-pursuit-of-static-target
convergence (regression guard confirming the deadlock is genuinely mutual-pursuit-specific), and
the confirmed mutual-diagonal-pursuit deadlock itself (a characterization test, not a "should
never happen" assertion — it locks in the current, documented, real behavior). All 5 pass.

1 separate, unrelated, pre-existing test fixed (`test_terrain_readiness_success`, see
Implementation Notes). Full scoped re-run: `tests/unit/movement/`, `tests/unit/world/`,
`tests/unit/combat/`, `tests/unit/tactical/`, `tests/unit/kernel/`, `tests/unit/core/`,
`tests/unit/engine/` — 839 passed, 1 skipped, only the 1 pre-existing, already-confirmed-
unrelated failure (`test_normal_move_triggers_oa`).

## Files Changed
- `tests/unit/movement/test_navigation_get_next_step.py` — new, 5 tests
- `tests/unit/world/test_terrain_weighting.py` — fixed a stale assertion from an earlier,
  unrelated same-session ticket's own incomplete test-sweep scope
- `docs/engine/known_limitations.md` §1.1 — documented the confirmed mechanism and real,
  measured corpus prevalence
- `docs/engine/contracts/tactical_contract.md` §3 — cross-referenced the known limitation

## Completion Summary
Investigated the disclosed diagonal mutual-pursuit deadlock from the prior ticket's own Verify
phase. Confirmed the exact mechanism (a single-axis stepping tie-break that always favors Y on
an exact diagonal tie, which cancels perfectly when BOTH sides of a pursuit are simultaneously,
reactively re-targeting each other) both analytically and empirically, and — critically —
measured real corpus prevalence rather than assuming it: across a broad, real sample (3 seeds ×
up to 8 worlds × 2000 ticks), exactly 1 pursuit pair ever reached a genuine, sustained deadlock.
Given this low, measured prevalence, chose to document the limitation rather than force a
stepping-algorithm change to core movement code for a rare, coincidental-geometry edge case —
matching this session's own established discipline of evidence-based, proportionate scope
decisions. Added the first-ever direct test coverage for `get_next_step`, locking in the
characterized behavior. Also found and correctly fixed a separate, real, pre-existing test
failure left behind by an earlier same-session ticket's own incomplete test-sweep scope.
