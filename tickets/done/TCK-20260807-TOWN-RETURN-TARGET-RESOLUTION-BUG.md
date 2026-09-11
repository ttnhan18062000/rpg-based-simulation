---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG
phase: done
date: 2026-08-07
tags: [strategy, simulation-quality]
---

# TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG

## Title
`TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER`'s own reach_location objectives never resolve a
navigable position — `TacticalDecisionSystem._resolve_target_position()` can't parse
`target_id="town_center"`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s real-kernel investigation, confirmed
via direct monkeypatch tracing of the live function during a real 280-tick run:
`TownScorer.score()` (`src/ai/goals/scorers.py`) sets `GoalScore(kind=GoalKind.TOWN_RETURN,
target_id="town_center", target_pos=state.town_center)` — but
`TacticalDecisionSystem._resolve_target_position()` (`src/engine/tactical.py:694-728`), the
function that turns a `reach_location` objective's `target` field into an actual world position
for arrival-dispatch, only parses an int-castable resource-node/building ID or a stringified
coordinate tuple. `"town_center"` is neither — `_resolve_target_position` returns
`(None, None, None)` for every `town_return` objective, every time (confirmed empirically, not
assumed: every call logged during a live run returned `None`).

**Practical effect**: `TOWN_RETURN` projects are created (the goal DOES win competitively) but can
never complete via `tactical.py`'s arrival-dispatch path (`if target_pos:` gates the entire
block, including movement-target-setting) — the entity effectively idles strategically on this
goal (real position drift observed during the parent ticket's investigation turned out to be from
an unrelated combat anti-stalemate fallback that coincidentally also targets `(0.0, 0.0)`, the
same value as `town_center` in every sampled world — a red herring).

**`RecoverScorer`** (`scorers.py:186`) uses the identical `target_id="town_center"` pattern —
affected identically. **`ResolveBlockerScorer`** (`scorers.py`, final fallback) sets
`target_pos = state.town_center` directly but `target_id=str(blocker.id)` (a blocker ID, not a
resource-node/building ID) — `_resolve_target_position`'s int-parse succeeds but neither
`state.resource_nodes` nor `state.buildings` will contain a matching entry, so `target_pos` is
also `None` via this path. All three scorers are affected by the same underlying
convention mismatch between how `GoalScore.target_id` is populated and what
`_resolve_target_position` can parse.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the exact fix: either (a) make `_resolve_target_position` also check
     `obj.target_position` directly when `obj.target` fails to parse (mirrors
     `_resolve_active_objective`'s own existing "detour" case,
     `intelligence.py:1030-1044`, which already prefers `target_position` first — the two
     "resolve an objective's position" implementations have diverged), or (b) change the 3
     affected scorers to encode `target_id` as a parseable coordinate string instead. Prefer (a)
     — it's the less invasive fix and aligns two already-existing implementations rather than
     changing 3 call sites' own established `target_id` semantics.
   - Confirm this fix doesn't change behavior for any CURRENTLY-working reach_location objective
     (`HarvestScorer`/`CombatEngageScorer`/`EatScorer`/`SleepScorer`/`GuildNeedScorer`, all of
     which use real int-castable IDs) — should be a pure addition (a new fallback path), not a
     change to the existing int/tuple-parsing branches.
2. **Plan**: design the exact fix.
3. **Implement**: apply it; add regression tests confirming `TOWN_RETURN`/`RECOVER`/
   `RESOLVE_BLOCKER` projects now resolve a real target position and can complete via arrival
   (or, if arrival-dispatch itself needs a corresponding fix for these kinds too, disclose that
   as a further, separate finding rather than silently expanding scope).
4. Real-kernel verification: confirm entities with `TOWN_RETURN`/`RECOVER` projects now actually
   navigate toward and reach `town_center` in a real run.

## Out of Scope
- `GuildNeedScorer`/`GuildVisitPhase` (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`) — already
  fixed independently, using a different (unaffected) convention.
- Any change to `tactical.py`'s existing `hunger`/`fatigue` arrival-dispatch branches, or what
  happens once `TOWN_RETURN`/`RECOVER` DO arrive (that's a separate question from "can it ever
  navigate there at all," which is this ticket's own scope).

## Acceptance Criteria
- [x] `investigation.md` confirms the exact fix location and design
- [x] Fix implemented; `_resolve_target_position` now resolves a real position for
      `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` objectives (via a `target_position` fallback)
- [x] Regression test confirming existing int/tuple-based reach_location resolution is unaffected
      (`test_reach_location_target_position_fallback_does_not_override_resolvable_node_id`)
- [x] Real-kernel(-adjacent) verification: real `evaluate_strategic_intent()` →
      `evaluate_entity_intent()` call sequence confirms a `TOWN_RETURN` project now produces a
      real `NavigationUpdate` toward `town_center`, codified as a permanent regression test
- [x] Scoped pytest run passes (247/248; 1 pre-existing unrelated failure confirmed via git stash)

## Related Tickets
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING (found this, DONE — used a different, unaffected
  target-encoding convention to route around it rather than fix it inline)

## Related Docs
None specific — no Mechanics Bible chapter formalizes goal-target-resolution as a law (confirmed
during the parent ticket's own investigation).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING/investigation.md` (the finding and
  its empirical confirmation via monkeypatch tracing)

## Related Code Areas
- `src/engine/tactical.py` (`TacticalDecisionSystem._resolve_target_position`)
- `src/ai/goals/scorers.py` (`TownScorer`, `RecoverScorer`, `ResolveBlockerScorer`)
- `src/systems/strategic_systems/intelligence.py` (`_resolve_active_objective`'s own parallel,
  already-correct "detour" pattern — the fix's likely template)

## Assumptions / Open Questions
- Whether fixing this also requires extending `tactical.py`'s arrival-dispatch branch (currently
  only recognizes `hunger`/`fatigue` project kinds at a building) for `TOWN_RETURN`/`RECOVER` to
  do anything useful once they DO arrive — not assumed either way; if navigation resolution alone
  doesn't produce an observable behavior change (entities arrive but then just idle, same as
  `GUILD` did before its own dedicated arrival-phase was added), this ticket's own Investigate
  phase should surface that as a related, but likely separate, finding.

## Implementation Notes
`TacticalDecisionSystem._resolve_target_position()` (`src/engine/tactical.py`) now falls back to
`obj.target_position` when the existing int-castable-ID parse and coordinate-string parse of
`obj.target` both fail to yield a position. This mirrors
`StrategicIntelligenceSystem._resolve_active_objective()`'s own pre-existing "detour" case, which
already preferred `target_position` this same way — the two "resolve an objective's position"
implementations are now aligned. The fallback is purely additive: the int-parse attempt is always
tried first, so `node_id`/`building_id` population for the currently-working
`HarvestScorer`/`EatScorer`/`SleepScorer`/`GuildNeedScorer` paths (needed for their
INTERACT/EAT/REST arrival-dispatch) is completely unchanged — verified by a dedicated
anti-regression test that deliberately sets a wrong `target_position` alongside a real resolvable
node ID and confirms the resolvable ID still wins.

Arrival-dispatch for `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` once they DO arrive is explicitly
NOT extended in this ticket (per its own Out-of-Scope) — these objectives now navigate to a real
position but still resolve to a bare idle `EntityUpdate` at arrival, since `node_id`/`building_id`
stay `None` for the `target_position`-only path. Disclosed in investigation.md and
`docs/engine/contracts/tactical_contract.md`'s new Section 7, not filed as a further follow-up
ticket since the intended arrival behavior is itself an open game-design question, not a clear
wiring gap.

## Test Summary
New tests: `tests/unit/tactical/test_objective_pursuit_coverage.py`
(`test_reach_location_with_unparseable_target_id_falls_back_to_target_position`,
`test_reach_location_with_unparseable_target_id_and_no_target_position_stays_unresolved`,
`test_reach_location_target_position_fallback_does_not_override_resolvable_node_id`) and
`tests/unit/strategic/test_expanded_goals.py`
(`test_town_return_project_now_produces_real_navigation`, a real end-to-end production-pipeline
integration test). All new and pre-existing tests in both files pass (7/7, 8/8). Wider regression
sweep (`tests/unit/tactical/`, `tests/unit/strategic/`, `tests/unit/movement/`,
`test_tactical_hardening.py`, `test_tactical_legality.py`): 247/248 pass — the 1 failure
(`test_normal_move_triggers_oa`, an opportunity-attack combat mechanic in `MovementSystem`) is
pre-existing and unrelated, confirmed via `git stash` on this ticket's own changed files (fails
identically on the clean baseline).

## Files Changed
- `src/engine/tactical.py` — `_resolve_target_position()`'s `target_position` fallback
- `tests/unit/tactical/test_objective_pursuit_coverage.py` — 3 new tests
- `tests/unit/strategic/test_expanded_goals.py` — 1 new end-to-end integration test
- `docs/engine/contracts/tactical_contract.md` — new Section 7, "Objective Target Resolution"
- `docs/parity_ledger/strategic_cognition.yaml` — new `STRAT-249` entry

## Completion Summary
Fixed the confirmed root cause: `TownScorer`/`RecoverScorer` (no-inn fallback)/`ResolveBlockerScorer`
all set an objective's `target` field to a value `_resolve_target_position` could never parse
(`"town_center"`, or a non-coordinate blocker ID), even though the real position was already
carried on the same objective's `target_position` field the whole time. These 3 goal kinds now
produce real navigation toward their intended target, verified end-to-end against the real,
unmocked `evaluate_strategic_intent()`/`evaluate_entity_intent()` production pipeline pair, not
just a unit-level mock. Arrival-dispatch behavior once these objectives DO arrive remains
unextended, honestly disclosed as a separate, deferred question (the intended in-town/
blocker-resolution behavior is itself undecided game design, not a mechanical gap like `GUILD`'s
was) rather than silently assumed or guessed at.
