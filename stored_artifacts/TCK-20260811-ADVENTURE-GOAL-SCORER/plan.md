---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-ADVENTURE-GOAL-SCORER
artifact_type: plan
tags: [cognition, adventure]
---

# Implementation Plan — TCK-20260811-ADVENTURE-GOAL-SCORER

## Summary

Add `GoalKind.ADVENTURE_ROUTE` to `src/core/strategic.py`, a new `AdventureGoalScorer` class in a
new `src/ai/goals/adventure_scorer.py` module that replicates the opportunities → generate →
decide sequence `AdventureDecisionPhase.apply()` already runs per-hero (`src/domains/adventure/
phase.py:154-167`) for a single entity, normalizes the raw ~0-2.9 route score onto the 0-100
`GoalScore.utility` scale, and carries the raw score + route family in `GoalScore.metadata`.
Register it in `src/ai/goals/__init__.py`. Add a new materialization branch in
`StrategicIntelligenceSystem.evaluate_strategic_intent()` (`src/systems/strategic_systems/
intelligence.py`) that calls `RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...)`
instead of the generic `ObjectiveState`/`ProjectState` construction, when the tier-5 winner is
`GoalKind.ADVENTURE_ROUTE` — never `best_candidate.utility`, which is on the wrong scale for a
mapped `ProjectKind`-typed project. This plan makes three decisions investigation.md flagged as
blocking:

- **Risk #1 (target/target_pos gap)**: resolved as **(a) synthesize a placeholder `target_id`**
  (`f"adventure:{family.value}"`) **paired with a real, resolvable `target_pos`** inside
  `AdventureGoalScorer.score()` for the three route families (`RECOVER` forced,
  `ASK_INFORMATION` forced, `FORM_PARTY`) that `AdventureRouteGenerator.generate()` never backs
  with `target_node_id`/`source_opportunity_ids`. **Revised after an architecture-reviewer pass
  (2026-08-11) found the original version of this plan synthesized `target_id` alone, leaving
  `target_pos=None` — which clears the tier-5 floor gate but then produces a committed project
  that can never make tactical progress (traced through
  `TacticalDecisionSystem._resolve_target_position()`/`tactical.py`'s arrival-dispatch guard) —
  "wins but stalls forever."** The fix now pairs `target_id` with a real `target_pos` sourced the
  same way `RecoverScorer`/`TownScorer` already do (`src/ai/goals/scorers.py:98,163,186`, read
  directly), so the existing `target_position` fallback in
  `TacticalDecisionSystem._resolve_target_position()` (`src/engine/tactical.py:751-752`, read
  directly) resolves it into real navigation, per `docs/engine/contracts/tactical_contract.md`
  §7 ("Objective Target Resolution") — not currently cited in investigation.md, added here as
  load-bearing. See "Unresolved Questions Now Resolved" below for the full justification and the
  concrete per-family data sources.
- **Risk #5 (tie-break value)**: resolved as the literal string `"z_adventure_route"`.
- **Risk #4 (double `map_to_states()` call)**: resolved as the double-call approach, matching
  AC3's literal wording — `decide()`'s own internal `map_to_states()` call
  (`service.py:141-148`) stays unused for materialization; `intelligence.py`'s new branch calls
  `RouteToProjectMapper.map_to_states()` a second time using `metadata["route_family"]`/
  `metadata["raw_score"]`, not `decide()`'s `proposed_project`/`proposed_objective`.

A previously undocumented circular-import hazard was found during fact-verification for this
plan (not flagged in investigation.md): `intelligence.py:77` does a top-level
`from src.ai.goals import GoalRegistry`, which — once `adventure_scorer.py` is registered in
`src/ai/goals/__init__.py` — means loading `src.ai.goals` can trigger loading `intelligence.py`
as a side effect, and vice versa. Step 2 resolves this by making `AdventureGoalScorer.score()`'s
imports of `intelligence.py`'s two constants and `phase.py`'s eligibility helper lazy
(function-local), matching the codebase's own existing convention (every scorer in
`scorers.py` already does function-local imports for cross-module concerns, e.g.
`SpatialQueryService` inside `RecoverScorer.score()`, `scorers.py:181`) rather than a top-level
import that depends on module-init ordering.

## Unresolved Questions Now Resolved (do not re-litigate in Implement)

**Risk #1 — target/target_pos gap for RECOVER(forced)/ASK_INFORMATION(forced)/FORM_PARTY.**
Chosen: **(a) synthesize a placeholder `target_id` paired with a real, resolvable `target_pos`**,
not (b) accept as permanently unwinnable. Justification against the ticket's own text and the
design doc:
- The ticket's AC5 says: *"Ineligible entities and DEFER_WITH_REASON results produce
  GoalScore(utility=0, target_id=None) that never clears the 20.0 tier-5 floor"* — this names
  exactly two categories as intentionally unwinnable. It does not say "and 3 of the 15 route
  families." Choosing (b) would silently make AC5's own framing incomplete/misleading — a
  contradiction between the AC's stated scope and the actual implemented behavior, which the
  planner's fact-verification duty requires resolving before Implement, not after.
- The design doc's Goal #3 (`docs/architecture/2026-08-11-adventure-as-cognition-strategy-
  subcomponent-design.md:55-57`) states: *"Adventure becomes correctly subject to the same
  strategic hierarchy ... every other decision already respects — closing a gap where it was
  invisible to that hierarchy entirely."* Permanently excluding 3 of 15 route families from ever
  winning tier 5 (regardless of eligibility, urgency, or score) reproduces exactly the kind of
  structural invisibility Goal #3 says this design closes — just narrowed to 3 families instead
  of all 16.
- The design doc's own worked decision-tree diagram (`docs/architecture/2026-08-11-....md:518,
  528`) illustrates `FORM_PARTY` (`raw_score=2.1`) as the tier-5 *winner*, materialized via
  `RouteToProjectMapper`. The design's own canonical example assumes `FORM_PARTY` can win — it
  does not flag `FORM_PARTY` as structurally incapable of clearing the floor gate. Choosing (b)
  would make the design doc's own flagship worked example impossible under the implementation
  that supposedly realizes it.
- The Anti-Drift Hazards in investigation.md explicitly permit fixing this *inside*
  `AdventureGoalScorer.score()`'s own target_id construction, and explicitly forbid weakening the
  shared floor gate — option (a) does exactly that (fix in the scorer, not the gate).

**Reviewer correction (2026-08-11, applies on top of the above): `target_id` alone is not
sufficient — `target_pos` must also be real.** An earlier version of this plan synthesized only
`target_id`, leaving `target_pos=None`. That clears `intelligence.py:1373`'s target-presence
check (`target_id OR target_pos` non-None) but does **not** clear the separate, later hazard the
architecture-reviewer traced end-to-end: `RouteToProjectMapper.map_to_states()`
(`src/domains/adventure/mapper.py:88-95`, read directly) commits `target_pos=None` verbatim into
`ObjectiveState.target_position`. `TacticalDecisionSystem._resolve_target_position()`
(`src/engine/tactical.py:702-753`, read directly) then tries `int("adventure:form_party")`
(fails), `ast.literal_eval(...)` (fails), and falls back to `obj.target_position`
(`tactical.py:751-752`) — which is `None`, so the function returns `(None, None, None)`. For
`FORM_PARTY` specifically (mapped to `ObjectiveKind.REACH_LOCATION` — confirmed
`mapper.py:42`), `tactical.py`'s `if obj.kind == "reach_location" and obj.target:` branch
(`tactical.py:218`) is entered (since `target_id` is truthy), but its inner `if target_pos:`
guard (`tactical.py:221`) is then False, so the entire arrival-dispatch block — including the
`else: navigate toward target_pos` branch (`tactical.py:257-263`) that would otherwise move the
entity — is silently skipped every tick. **Net effect without a real `target_pos`: the
synthesized candidate wins tier-5 arbitration, locks the project slot, and the entity never even
starts navigating — it stalls forever**, contradicting this very justification's own point above
(that (a) must make adventure "correctly subject to the same strategic hierarchy," not just
nominally clear one gate while remaining functionally invisible downstream).

**The fix**: pair the synthesized `target_id` with a real `target_pos`, sourced the same way the
codebase's own working precedent already does it — `TownScorer`/`CombatRetreatScorer` pair
`target_id="town_center"` with `target_pos=state.town_center`
(`src/ai/goals/scorers.py:98,163`, read directly); `RecoverScorer` pairs a real building id (or
`"town_center"`) with `target_pos=best_bldg.position` or `state.town_center`
(`scorers.py:181-186`, read directly). With a real `target_pos`, `_resolve_target_position()`'s
node-3 fallback (`tactical.py:751-752`) resolves it into real navigation — `node_id`/`building_id`
stay `None` (same documented, accepted limitation `tactical_contract.md` §7 already describes for
`TownScorer`'s own `"town_center"` winners: "objective resolved only via the `target_position`
fallback still navigates to the position, but arrival dispatches to a bare idle `EntityUpdate`
rather than INTERACT/EAT/REST" — not a new gap this ticket introduces, an existing, accepted one
this ticket's 3 families now share with `TownScorer`). This is a materially different outcome
from "wins but stalls forever": the entity **does** navigate to a real position and, on arrival,
receives the same accepted idle-arrival behavior `TownScorer` winners already receive today — real
tactical progress, not a permanent dead lock. See Step 2 for the concrete per-family `target_pos`
sources and Step 5/Step 6 for the new tests that verify this end-to-end via
`TacticalDecisionSystem._resolve_target_position()` directly, not just `target_id is not None`.

**Risk #5 — tie-break literal value.** Chosen: `GoalKind.ADVENTURE_ROUTE = "z_adventure_route"`.
Confirmed (`src/core/strategic.py:121-133`, read directly) the 10 existing `GoalKind` values are:
`harvesting, fatigue, hunger, social, town_return, combat_engage, combat_retreat, recover,
resolve_blocker, guild`. Every one of these begins with a letter in `c`-`t`. Any string beginning
with `z` sorts after all of them in Python's default lexicographic string comparison regardless of
the rest of the string (`'z' > 'c'`, `'z' > 't'`, etc. — the first differing character alone
decides the comparison), so `"z_adventure_route"` is guaranteed to sort after all 10 current
values and, by construction, after any value in the `a`-`y` range a future ticket might add too
(not just `"town_return"` specifically) — a stronger guarantee than "sorts after town_return"
alone.

**Risk #4 — double `map_to_states()` call.** Chosen: the double-call approach (AC3's literal
wording), not threading `decide()`'s pre-built `proposed_project`/`proposed_objective` through
metadata. `decide()`'s own internal `map_to_states()` call (`service.py:141-148`, confirmed read
directly) already runs unconditionally as part of calling `decide()` unchanged — its result
(`result.proposed_project`/`result.proposed_objective`) is simply never read by this plan's Step 2
or Step 4. Both calls use `tick == current_tick` within the same
`evaluate_strategic_intent()` invocation (Step 2 calls `decide(..., tick=state.tick, ...)`; Step 4
calls `map_to_states(..., tick=current_tick, ...)`; both are the same tick value by construction),
so the two calls are deterministic and produce byte-identical `ProjectState`/`ObjectiveState` IDs
and content — real but harmless duplication, not a correctness risk.

## Steps

### Step 1 — Add `GoalKind.ADVENTURE_ROUTE` enum member

**Files:** `src/core/strategic.py`

**Change:** In the `GoalKind(str, Enum)` class body (confirmed exact current contents, read
directly, lines 121-132: 10 members `HARVESTING` through `GUILD`, no trailing comma issue), add
one new member immediately after `GUILD = "guild"` (line 132):
```python
    ADVENTURE_ROUTE = "z_adventure_route"  # deliberately sorts after all 10 existing GoalKind
    # values (Risk #5): starts with 'z', so it never wins an exact-utility tie against any other
    # GoalKind under intelligence.py:1369's `sort(key=lambda x: (-x.utility, x.kind))` — see
    # plan.md "Unresolved Questions Now Resolved" for the full worked rationale.
```

**Do NOT touch:** The 10 existing members' values (`"harvesting"`, `"fatigue"`, etc. — read
directly, confirmed unchanged verbatim) or `ProjectKind` (defined immediately below, line 135,
confirmed a separate class — do not merge or cross-reference the two enums, D22's unification
work is explicitly out of scope per the ticket).

**Verify:** `test_goal_kind_adventure_route_is_registered_member`,
`test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds`,
`test_adventure_route_loses_exact_utility_tie_against_existing_kind` (all in
`tests/unit/ai/goals/test_adventure_goal_scorer.py`).

---

### Step 2 — Create `AdventureGoalScorer` in a new module

**Files:** `src/ai/goals/adventure_scorer.py` (new file)

**Change:** Create the file with the following structure (exact shape, not paraphrase):

```python
from __future__ import annotations
from typing import Dict, Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import GoalKind
from src.domains.adventure.schema import RouteFamily

# Per-process cache of cognition_profile_id -> supports_adventure_routing, shared across all
# entities and ticks. phase.py's own _supports_adventure_routing(entity, cache) expects a
# cache dict shared across one AdventureDecisionPhase.apply() call (phase.py:83-96, confirmed
# read directly: "cache is a per-apply()-call dict keyed by cognition_profile_id"). This scorer
# is invoked once per entity per tick via GoalRegistry.get_all_scores(entity, state)
# (base.py:46-50) -- there is no natural per-tick shared cache object at this call site
# (investigation.md Risk #3). Cognition profile definitions are static content for the run's
# duration, so a module-level dict persisting across ticks is a safe substitute, not a
# correctness risk.
_PROFILE_ELIGIBILITY_CACHE: Dict[str, bool] = {}


class AdventureGoalScorer(GoalScorer):
    """
    GoalScorer wrapper around AdventureDecisionService.decide() (src/domains/adventure/
    service.py), registered under GoalKind.ADVENTURE_ROUTE as one candidate among many in tier 5
    of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py:1355). See
    docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        # Lazy import: src/systems/strategic_systems/intelligence.py:77 does a top-level
        # `from src.ai.goals import GoalRegistry`, which (once this module is registered in
        # src/ai/goals/__init__.py) means loading src.ai.goals can trigger loading
        # intelligence.py as a nested side effect, and vice versa. A transitive import path
        # back from phase.py DOES exist (corrected 2026-08-11 -- the earlier claim that no such
        # path exists was factually wrong and has been struck): phase.py:20 does
        # `from src.systems.strategic import StrategicIntelligenceSystem`; src/systems/
        # strategic.py (confirmed read directly) is a one-line compatibility shim doing
        # `from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem`;
        # and intelligence.py:77 is the same `from src.ai.goals import GoalRegistry` line cited
        # above. So phase.py -> src.systems.strategic -> src.systems.strategic_systems.
        # intelligence -> src.ai.goals is a real, confirmed transitive path. The lazy-import
        # pattern below is precisely what keeps that path safe -- deferring both this import and
        # the constants import to call time (after all modules have finished loading) means
        # neither one depends on which module happens to trigger the load chain first,
        # regardless of how many hops the transitive path has. This import is deferred for the
        # same reason as the constants import below, not because the path doesn't exist.
        from src.domains.adventure.phase import _supports_adventure_routing

        if not _supports_adventure_routing(entity, _PROFILE_ELIGIBILITY_CACHE):
            return GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=0.0, target_id=None)

        # MUST be a lazy (function-local) import, not top-level: intelligence.py's own
        # top-level `from src.ai.goals import GoalRegistry` (intelligence.py:77) means a
        # top-level import here of intelligence.py's constants would depend on which module
        # happens to be imported first process-wide -- a fragile, easy-to-silently-break
        # ordering dependency. Deferring to call time (after all modules have finished
        # loading at import time) removes the fragility entirely. Matches this codebase's own
        # established convention: every scorer in src/ai/goals/scorers.py already does
        # function-local imports for cross-module concerns (e.g. SpatialQueryService imported
        # inside RecoverScorer.score(), scorers.py:181).
        from src.systems.strategic_systems.intelligence import (
            _ADVENTURE_ROUTE_SCORE_MAX,
            _GOAL_UTILITY_SCORE_MAX,
        )
        from src.domains.adventure.generator import AdventureRouteGenerator
        from src.domains.adventure.service import AdventureDecisionService
        from src.world.providers.resources import ResourceOpportunityProvider
        from src.world.providers.services import ServiceOpportunityProvider

        # Replicates phase.py:154-167's opportunities -> generate -> decide sequence exactly,
        # for this single entity. All three calls are unchanged (confirmed by reading
        # generator.py, service.py, phase.py directly). faction_directives is NOT threaded
        # through here: unlike AdventureDecisionPhase.apply() (pipeline.py:238-244), which
        # receives it as a pipeline-level artifact computed earlier in the same tick by
        # FactionDecisionPhase.execute() (pipeline.py:181, confirmed read directly -- NOT an
        # attribute of AuthoritativeState, so there is no `state.faction_directives` to read),
        # there is no natural source for it at this GoalScorer.score(entity, state) call
        # signature. decide()'s own faction_directives parameter already defaults to None
        # (service.py:36), so passing None here is a disclosed simplification, not a silent
        # gap: this scorer is unwired from pipeline.py in this ticket's scope (ticket Out of
        # Scope), so no live behavior depends on this yet -- C3 (the wiring ticket) must decide
        # whether/how to thread real faction directives once this path goes live.
        opportunities = (
            ResourceOpportunityProvider.get_opportunities(entity, state)
            + ServiceOpportunityProvider.get_opportunities(entity, state)
        )
        candidates = AdventureRouteGenerator.generate(entity, state, opportunities=opportunities)
        result = AdventureDecisionService.decide(
            entity,
            candidates,
            tick=state.tick,
            resource_nodes=state.resource_nodes,
            faction_directives=None,
            factions=state.factions,
        )

        selected = result.selected
        if selected is None or selected.family == RouteFamily.DEFER_WITH_REASON:
            # AC5: ineligible/DEFER_WITH_REASON never clear the 20.0 tier-5 floor.
            return GoalScore(
                kind=GoalKind.ADVENTURE_ROUTE,
                utility=0.0,
                target_id=None,
                metadata={
                    "route_family": RouteFamily.DEFER_WITH_REASON,
                    "raw_score": selected.score if selected else 0.0,
                },
            )

        raw_score = selected.score
        family = selected.family

        # Risk #1 resolution (plan.md decision, REVISED 2026-08-11 after an
        # architecture-reviewer pass -- fix belongs here, in the scorer's own target_id/
        # target_pos construction, NOT in the shared floor gate at intelligence.py:1373, per
        # investigation.md's Anti-Drift Hazards). RECOVER (forced, generator.py:98-109),
        # ASK_INFORMATION (forced, generator.py:111-123), and FORM_PARTY (always,
        # generator.py:125-163) never populate target_node_id/source_opportunity_ids
        # (confirmed by reading generator.py directly). decide() then leaves target=None
        # (service.py:134-140) and target_pos is never set at all, for any route
        # (service.py:135, confirmed unconditional). Left as-is, these three families would
        # always fail intelligence.py:1373's target-presence check regardless of utility.
        #
        # Synthesizing target_id ALONE is not sufficient (this was the plan's original,
        # reviewer-rejected version): it clears the target-presence check but leaves
        # target_pos=None, which RouteToProjectMapper.map_to_states() (mapper.py:88-95) commits
        # verbatim into ObjectiveState.target_position, and
        # TacticalDecisionSystem._resolve_target_position() (tactical.py:702-753) can never
        # recover from int()/ast.literal_eval() parsing since target_id is neither -- its only
        # remaining fallback IS target_position (tactical.py:751-752), which is also None. The
        # committed project then wins tier-5 arbitration and locks the slot, but tactical.py's
        # `if target_pos:` guard (tactical.py:221, and again at 275 for the non-REACH_LOCATION
        # branch) is False every tick, so the entity never even starts navigating -- it stalls
        # forever. This is the exact "wins but stalls" defect the reviewer traced end-to-end.
        #
        # Fix: pair the placeholder target_id with a REAL target_pos, sourced the same way the
        # codebase's own working precedent already does it -- TownScorer pairs
        # target_id="town_center" with target_pos=state.town_center (scorers.py:98);
        # RecoverScorer pairs a real building id (or "town_center") with
        # target_pos=best_bldg.position or state.town_center (scorers.py:181-186). With a real
        # target_pos, _resolve_target_position()'s node-3 fallback (tactical.py:751-752)
        # resolves it into real navigation -- node_id/building_id stay None, which is the SAME
        # documented, accepted limitation tactical_contract.md §7 already describes for
        # TownScorer's own "town_center" winners (arrival dispatches to a bare idle EntityUpdate,
        # not INTERACT/EAT/REST) -- not a new gap, an existing accepted one these 3 families now
        # share with TownScorer. This makes the candidate genuinely tactically actionable
        # (navigates, then reaches the same accepted idle-arrival state TownScorer winners already
        # reach) instead of a permanent dead lock.
        if selected.target_node_id is not None:
            target_id = str(selected.target_node_id)
            target_pos = None
        elif selected.source_opportunity_ids:
            target_id = selected.source_opportunity_ids[0]
            target_pos = None
        else:
            target_id = f"adventure:{family.value}"
            target_pos = AdventureGoalScorer._resolve_placeholder_target_pos(family, entity, state)

        utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX

        return GoalScore(
            kind=GoalKind.ADVENTURE_ROUTE,
            utility=utility,
            target_id=target_id,
            target_pos=target_pos,
            metadata={"route_family": family, "raw_score": raw_score},
        )

    @staticmethod
    def _resolve_placeholder_target_pos(
        family: RouteFamily, entity: EntityState, state: AuthoritativeState
    ) -> Optional[Tuple[float, float]]:
        """
        Real target_pos source for the 3 route families that never carry a
        target_node_id/source_opportunity_ids (see the Risk #1 comment block in score() above).
        Mirrors the SAME real data sources RecoverScorer/TownScorer already use
        (src/ai/goals/scorers.py:98,163,186, confirmed read directly) -- deliberately not a
        synthetic placeholder position, per the architecture-reviewer's explicit instruction to
        "read RecoverScorer/TownScorer directly to see what real position data they pull from
        entity/state, and use the same kind of real, available field."
        """
        from src.domains.adventure.schema import RouteFamily as _RF

        if family == _RF.RECOVER:
            # Same source as RecoverScorer's own no-target_node_id path (scorers.py:181-186):
            # nearest inn if one exists, else town_center. "Recovering" plausibly means going to
            # a place of rest, not staying in place -- mirrors the existing scorer exactly rather
            # than inventing a new convention.
            from src.engine.spatial_query import SpatialQueryService
            best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "inn")
            return best_bldg.position if best_bldg else state.town_center

        if family == _RF.ASK_INFORMATION:
            # Same source as TownScorer's target_pos (scorers.py:98): information-gathering is a
            # town-centered activity in this codebase's existing convention (no dedicated
            # "information source" building exists in the real content corpus -- confirmed by
            # GuildNeedScorer's own docstring, scorers.py:233, noting no world ever declares a
            # dedicated "guild" building either, and using town_hall/town_center instead).
            return state.town_center

        if family == _RF.FORM_PARTY:
            # Real ally position, mirroring generator.py's OWN FORM_PARTY candidate-eligibility
            # filter exactly (generator.py:126-137, confirmed read directly: non-self,
            # non-MONSTER role, alive). generator.py only generates a FORM_PARTY route when this
            # candidate list is non-empty (generator.py:138 `if candidates:`), and score() reads
            # the same `state` snapshot generate() just ran against synchronously within the same
            # call -- so a non-empty candidate list is expected here too. Nearest by Manhattan
            # distance, matching this codebase's existing nearest-selection convention (e.g.
            # CombatEngageScorer's `min(hostiles, key=...)`, scorers.py:113-117). Defensive
            # fallback to the entity's own current position (organizing/waiting in place) if,
            # against expectation, no candidate remains -- never re-raises or returns None, since
            # a None here would silently reproduce the exact "stalls forever" defect being fixed.
            from src.core.enums import EntityRole
            candidates = [
                e for e in state.entities.values()
                if e.id != entity.id
                and getattr(e.identity, "role", EntityRole.MONSTER) != EntityRole.MONSTER
                and getattr(e, "is_alive", True)
            ]
            if candidates:
                nearest = min(
                    candidates,
                    key=lambda e: abs(e.navigation.position[0] - entity.navigation.position[0])
                    + abs(e.navigation.position[1] - entity.navigation.position[1]),
                )
                return nearest.navigation.position
            return entity.navigation.position

        return None
```

Note on `metadata["route_family"]`'s type: store the actual `RouteFamily` enum member (not
`.value`), matching what `RouteToProjectMapper.map_to_states(family: RouteFamily, ...)`
(`mapper.py:69`, confirmed read directly) expects positionally in Step 4 — `map_to_states()`'s
own `get_kinds()` (`mapper.py:50-64`) is tolerant of either a `RouteFamily` member or its string
value (`RouteFamily(family)` re-construction, idempotent for an already-valid member), but storing
the enum member directly avoids an unnecessary re-parse at materialization time.

**Do NOT touch:** `src/domains/adventure/phase.py`, `service.py`, `generator.py`, `mapper.py`, or
`scoring.py` — every call into these is unchanged, per ticket scope and Anti-Drift Hazards. Do
not move `_resolve_cognition_profile_id`/`_supports_adventure_routing` out of `phase.py` (that is
the design doc's end-state relocation, explicitly deferred to the ticket that deletes
`AdventureDecisionPhase`) — import them, don't relocate them. Do not add `AdventureGoalScorer`'s
class body to `src/ai/goals/scorers.py` — it lives in its own new file specifically to avoid
giving the other 10 scorers a transitive import surface into `src/domains/adventure/`
(investigation.md, confirmed rationale). **Do not touch `src/engine/tactical.py`** —
`TacticalDecisionSystem._resolve_target_position()` and the arrival-dispatch guards at
`tactical.py:218-263` stay exactly as they are; the Risk #1 fix works entirely by supplying data
(`target_pos`) that satisfies their existing, unmodified `target_position` fallback contract
(`docs/engine/contracts/tactical_contract.md` §7), not by changing their logic. **Do not modify
`SpatialQueryService.nearest_building()`** (`src/engine/spatial_query.py`) — `_resolve_placeholder_
target_pos()` calls it read-only, exactly as `RecoverScorer` already does (`scorers.py:181-182`).

**Verify:** `test_adventure_goal_scorer_implements_goal_scorer_protocol`,
`test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact`,
`test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score`,
`test_adventure_goal_scorer_ineligible_entity_returns_zero_utility_no_target`,
`test_adventure_goal_scorer_defer_with_reason_returns_zero_utility_no_target`,
`test_form_party_winner_has_non_null_target_id_and_resolvable_target_pos`,
`test_forced_recover_winner_target_pos_resolves_to_inn_or_town_center`,
`test_forced_ask_information_winner_target_pos_resolves_to_town_center`,
`test_form_party_target_pos_falls_back_to_entity_own_position_when_no_ally_candidates` (all in
`tests/unit/ai/goals/test_adventure_goal_scorer.py`).

---

### Step 3 — Register `AdventureGoalScorer` in `src/ai/goals/__init__.py`

**Files:** `src/ai/goals/__init__.py`

**Change:** Confirmed current exact contents (read directly, 21 lines): imports `GoalKind` from
`src.core.strategic`, `GoalRegistry` from `src.ai.goals.base`, then 10 scorer classes from
`src.ai.goals.scorers`, then 10 `GoalRegistry.register(...)` calls. Add:
```python
from src.ai.goals.adventure_scorer import AdventureGoalScorer
```
as a new import line **placed after** `from src.ai.goals.base import GoalRegistry` (existing line
2) — this ordering matters (see Anti-Drift Notes: it is what makes the `GoalKind` symbol already
resolvable inside `src.ai.goals`'s own partially-initialized namespace if `intelligence.py`'s
nested `from src.ai.goals import GoalRegistry` import fires while `adventure_scorer.py` is being
loaded). Then add, after the 10 existing `GoalRegistry.register(...)` calls:
```python
GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer())
```

**Do NOT touch:** The 10 existing import/register lines — their order and content stay exactly as
confirmed read (`HarvestScorer` through `GuildNeedScorer`, in that order).

**Verify:** `test_goal_kind_adventure_route_is_registered_member` (registry-side half:
`GoalRegistry._scorers[GoalKind.ADVENTURE_ROUTE]` is an `AdventureGoalScorer` instance),
`test_all_registered_scorers_are_canonical` (`tests/unit/strategic/test_enum_drift.py`, existing
test, must keep passing with an 11th member).

---

### Step 4 — Add the `ADVENTURE_ROUTE` materialization branch

**Files:** `src/systems/strategic_systems/intelligence.py`

**Change (imports):** Confirmed current exact import block (read directly, lines 64-68):
```python
from src.core.strategic import (
    BlockerState, LeadState, LeadCertainty,
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    CognitionProfile, ProjectKind
)
```
Add `GoalKind` to this list (it is not currently imported here — confirmed by reading the block
directly; only `ProjectKind` is present). Also add a new top-level import (safe: confirmed by
reading `src/domains/adventure/mapper.py` directly — it imports only `src.core.strategic` and
`src.domains.adventure.schema`, neither of which imports back into `src.ai.goals` or
`src.systems.strategic_systems`, so this is not a circular-import risk the way the Step 2
constants import is):
```python
from src.domains.adventure.mapper import RouteToProjectMapper
```
placed near the existing `from src.ai.goals import GoalRegistry` (line 77) /
`from src.ai.score_modifiers import ScoreModifierSystem` (line 78) import group.

**Change (materialization branch):** Confirmed current exact lines 1401-1418 (read directly,
re-verified against investigation.md's own re-verified numbers — the design doc's earlier
"approximately lines 1397-1414" citation is off by a few lines and must not be used):
```python
            cand_kind_str = getattr(best_candidate.kind, "value", best_candidate.kind)
            obj = ObjectiveState(
                id=f"{cand_kind_str}_{best_candidate.target_id}",
                kind="reach_location",
                target=best_candidate.target_id,
                target_position=best_candidate.target_pos,
                status=ObjectiveStatus.ACTIVE
            )
            candidate_proj = ProjectState(
                id=f"proj_{cand_kind_str}_{current_tick}",
                kind=best_candidate.kind,
                status=ProjectStatus.ACTIVE,
                objectives=[obj],
                active_objective_id=obj.id,
                lock_until_tick=min(current_tick + 10, current_tick + 50),  # cap at 50 ticks
                created_tick=current_tick,
                score=best_candidate.utility
            )
```
Replace with:
```python
            if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:
                # AC3/AC4: materialize via RouteToProjectMapper using the RAW route score
                # (metadata["raw_score"]), never best_candidate.utility. _score_scale_max()
                # (intelligence.py:89-107) classifies a RouteToProjectMapper-mapped
                # ProjectState.kind (a real ProjectKind) onto the 2.9-ceiling scale, not the
                # 100-ceiling scale `utility` was normalized onto (Step 2's normalization is
                # ONLY for tier-5 competition, not for the committed ProjectState.score).
                # Passing `utility` here would reproduce the
                # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class --
                # see design doc Sec 4's worked-through scale-mismatch arithmetic.
                candidate_proj, obj = RouteToProjectMapper.map_to_states(
                    family=best_candidate.metadata.get("route_family"),
                    entity_id=entity.id,
                    target=best_candidate.target_id,
                    target_pos=best_candidate.target_pos,
                    tick=current_tick,
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
                if candidate_proj is None or obj is None:
                    # Preserves RouteToProjectMapper's existing (None, None) contract
                    # (mapper.py:81-82, confirmed: DEFER_WITH_REASON -> get_kinds() returns
                    # (None, None) -> map_to_states() returns (None, None)). Should not
                    # normally be reached here since DEFER_WITH_REASON never clears the tier-5
                    # floor (AC5, Step 2's early return), but this is a defensive no-op, not an
                    # assumption that the mapper always returns non-None.
                    if boredom_upd:
                        return StrategicUpdate(boredom_delta=boredom_upd)
                    return StrategicUpdate()
            else:
                cand_kind_str = getattr(best_candidate.kind, "value", best_candidate.kind)
                obj = ObjectiveState(
                    id=f"{cand_kind_str}_{best_candidate.target_id}",
                    kind="reach_location",
                    target=best_candidate.target_id,
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE
                )
                candidate_proj = ProjectState(
                    id=f"proj_{cand_kind_str}_{current_tick}",
                    kind=best_candidate.kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    lock_until_tick=min(current_tick + 10, current_tick + 50),  # cap at 50 ticks
                    created_tick=current_tick,
                    score=best_candidate.utility
                )
```
Everything from the original line 1420 onward (`at_capacity = len(strat.projects) >=
strat.profile.max_active_projects`, `evaluate_project_switch(entity, candidate_proj,
current_tick)`, etc.) stays **unchanged** and continues to reference `candidate_proj`/`obj` as
before — those two names are produced by both branches of the new `if`, so the rest of the
function needs no further edits.

**Other writers to `intelligence.py`'s materialization logic and `current_project_id` this step
must not collide with (enumerated per Fact-Verification Requirement #2):**
- `src/systems/social_systems/contracts.py:187` — unconditionally claims the project slot,
  bypassing `evaluate_project_switch()` entirely (per design doc's Context section). This step
  does not touch `contracts.py` and does not change whether it still bypasses the arbiter — that
  bypass is unaffected either way, explicitly out of scope (design doc's own Non-goals, "Future
  Extension Patterns").
- `src/systems/world_systems/events.py:98` (`stabilize_project`) — same unconditional-overwrite
  pattern, same "unaffected, out of scope" status.
- `src/domains/adventure/phase.py:192-194` (`AdventureDecisionPhase.apply()`'s own call to
  `StrategicIntelligenceSystem.evaluate_project_switch(hero, result.proposed_project, tick)`) —
  this is the *other* live writer that currently commits adventure-routed projects, through the
  arbiter, once per tick, for every adventure-eligible hero. This ticket's new tier-5
  `ADVENTURE_ROUTE` materialization branch runs in the **same** `evaluate_strategic_intent()`
  call as `AdventureDecisionPhase.apply()` (both execute every tick, since `pipeline.py:237-244`
  is unmodified and `AdventureGoalScorer` is registered but not wired into `pipeline.py`) — but
  because `AdventureGoalScorer` is never invoked from `pipeline.py` in this ticket's scope (only
  from `GoalRegistry.get_all_scores()`, which nothing calls except `evaluate_strategic_intent()`
  itself, tier 5), the new branch is **reachable but not fed any real winning `ADVENTURE_ROUTE`
  candidate through the live pipeline yet** — no double-write race exists today. This is a
  deliberately inert landing (design doc's own "migration step 1: land alongside the still-active
  `AdventureDecisionPhase`, registered but not wired"), not an oversight.
- `src/engine/tactical.py:194` and `src/pipeline_phases/guild_visit.py:88` — both only *clear*
  `current_project_id`, never write a competing project; unaffected by this step either way.

**Do NOT touch:** `evaluate_project_switch()`'s signature (`entity, candidate_project,
current_tick` — no `state` parameter, confirmed lines 928-933 unchanged) or its internal lock
logic — C2's job. Do not touch `pipeline.py`. Do not touch the `existing`/resume-suspended-project
branch at lines 1390-1399 (confirmed: it looks up `next((p for p in strat.projects.values() if
p.kind == best_candidate.kind), None)` — for an `ADVENTURE_ROUTE` winner this will essentially
always be `None`, since a *committed* adventure-routed project's `kind` is the real mapped
`ProjectKind`, never `GoalKind.ADVENTURE_ROUTE` itself; this means the resume-suspended-project
short-circuit never fires for adventure and no adventure-specific resume semantics exist yet —
this is pre-existing/acceptable, not a defect this ticket introduces or is required to fix).

**Verify:** `test_adventure_route_winner_materializes_with_raw_score_not_utility`,
`test_adventure_route_winner_preserves_none_none_handling_for_defer_family` (both in
`tests/unit/strategic/test_adventure_route_materialization.py`, new file).

---

### Step 5 — Unit tests for `AdventureGoalScorer`

**Files:** `tests/unit/ai/goals/test_adventure_goal_scorer.py` (new file, new directory
`tests/unit/ai/goals/` — confirmed no `__init__.py`-requiring package exists there today per
test_plan.md's own `ls` check)

**Change:** Implement, per test_plan.md's exact specifications, all of:
- `test_goal_kind_adventure_route_is_registered_member`
- `test_adventure_goal_scorer_implements_goal_scorer_protocol`
- `test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact` (parametrized:
  `raw_score=2.9 -> utility==100.0`, `raw_score=1.45 -> utility==50.0`,
  `raw_score=0.0 -> utility==0.0`; achieved by monkeypatching
  `AdventureDecisionService.decide` to return a controlled `AdventureDecisionResult` with a
  known `selected.score`)
- `test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score`
- `test_adventure_goal_scorer_ineligible_entity_returns_zero_utility_no_target` (spy-assert
  `AdventureDecisionService.decide` is never called)
- `test_adventure_goal_scorer_defer_with_reason_returns_zero_utility_no_target`
- `test_form_party_winner_has_non_null_target_id_and_resolvable_target_pos` — **replaces the
  test_plan.md placeholder test `test_form_party_winner_has_non_null_target_id_after_plan_
  resolves_risk_1`** (renamed to reflect that Risk #1's resolution was revised by an
  architecture-reviewer pass to require a real `target_pos`, not just a non-`None` `target_id` —
  see plan.md's "Unresolved Questions Now Resolved" for the full history). Set up a `state` with
  at least one non-self, non-`MONSTER`, alive entity in `state.entities` at a known position.
  Monkeypatch `AdventureDecisionService.decide` (or the generate/opportunities chain feeding it)
  to return a `FORM_PARTY`-family `AdventureRouteOption` with `target_node_id=None` and
  `source_opportunity_ids=()`. Call `AdventureGoalScorer().score(entity, state)` and assert
  **both**: `score.target_id == f"adventure:{RouteFamily.FORM_PARTY.value}"` (i.e.
  `"adventure:form_party"`, non-`None`, clears the `intelligence.py:1373` target-presence half of
  the floor check) **and** `score.target_pos == <the known ally position>` (non-`None`, the part
  the original plan version omitted). This is a unit-level check of the scorer's own output
  shape — Step 6 adds the deeper, tactical-resolution-level test.
- `test_forced_recover_winner_target_pos_resolves_to_inn_or_town_center` — force a `RECOVER`
  route with `target_node_id=None`/`source_opportunity_ids=()` (matching generator.py's forced
  path, generator.py:98-109) two ways: (1) with an inn building present in `state.buildings`,
  assert `score.target_pos == that inn's position`; (2) with no inn building, assert
  `score.target_pos == state.town_center`. Mirrors `RecoverScorer`'s own two-branch precedent
  (`scorers.py:181-186`) exactly.
- `test_forced_ask_information_winner_target_pos_resolves_to_town_center` — force an
  `ASK_INFORMATION` route with no `target_node_id`/`source_opportunity_ids` (matching
  generator.py's forced path, generator.py:111-123), assert `score.target_pos == state.town_center`.
- `test_form_party_target_pos_falls_back_to_entity_own_position_when_no_ally_candidates` —
  defensive case: force a `FORM_PARTY` route reaching `score()` (via monkeypatch, bypassing the
  normal generator-level `if candidates:` gate) with `state.entities` containing no eligible
  non-self/non-`MONSTER`/alive candidate, assert `score.target_pos == entity.navigation.position`
  (never `None` — a `None` here would silently reintroduce the "stalls forever" defect this
  revision fixes).
- `test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds`,
  `test_adventure_route_loses_exact_utility_tie_against_existing_kind` — per test_plan.md's exact
  bodies (already fully specified there), unchanged by this plan's Risk #5 resolution except that
  `GoalKind.ADVENTURE_ROUTE.value` now concretely equals `"z_adventure_route"`.

**Do NOT touch:** `tests/unit/strategic/test_expanded_goals.py`,
`tests/unit/strategic/test_score_normalization.py`, `tests/unit/strategic/test_enum_drift.py` —
these must keep passing unmodified (regression surface), not be edited to accommodate the new
scorer.

**Verify:** `pytest tests/unit/ai/goals/ -v` passes; all tests listed above pass.

---

### Step 6 — Integration tests for the materialization branch

**Files:** `tests/unit/strategic/test_adventure_route_materialization.py` (new file)

**Change:** Implement, per test_plan.md's exact specification:
- `test_adventure_route_winner_materializes_with_raw_score_not_utility` — monkeypatch
  `AdventureDecisionService.decide` to return a fixed high-confidence route with `raw_score=2.0`
  (so `utility = (2.0/2.9)*100.0 ≈ 68.97`), run
  `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)` end-to-end,
  assert the resulting `ProjectState.score == 2.0` (not `≈68.97`), assert
  `project.kind` is the real mapped `ProjectKind` (via `RouteToProjectMapper`, per Step 4's
  branch), not `GoalKind.ADVENTURE_ROUTE` itself.
- `test_adventure_route_winner_preserves_none_none_handling_for_defer_family` — force
  `metadata["route_family"] == RouteFamily.DEFER_WITH_REASON` reaching the materialization branch
  (defensive case) and assert no `StrategicUpdate.projects_add_or_update`-shaped commit results
  (no raise, no garbage `ProjectState`).
- **`test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall`** (new,
  added by this plan revision — the single test that directly proves the architecture-reviewer's
  finding is fixed, not just that `target_id` is non-`None`). Monkeypatch
  `AdventureDecisionService.decide` to return a `FORM_PARTY`-family route with
  `target_node_id=None`/`source_opportunity_ids=()`, with `state.entities` containing a real ally
  candidate at a known position distinct from the entity's own. Run
  `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)` end-to-end so
  the Step 4 materialization branch actually runs `RouteToProjectMapper.map_to_states()`. Then,
  **without touching `tactical.py`**, call
  `TacticalDecisionSystem._resolve_target_position(state, materialized_obj)` directly (import from
  `src.engine.tactical`) on the resulting `ObjectiveState` and assert:
  1. `materialized_obj.target_position is not None` (the committed `ObjectiveState` itself carries
     a real position, not `None` — this is the field the original, reviewer-rejected plan version
     left `None`).
  2. `_resolve_target_position(state, materialized_obj)` returns `(target_pos, None, None)` where
     `target_pos` equals the known ally position — i.e. resolution succeeds via the documented
     `target_position` fallback (`tactical.py:751-752`, `tactical_contract.md` §7 node 3), not via
     `int()`/`ast.literal_eval()` (both of which must fail for `"adventure:form_party"`, confirming
     the fallback path — not an accidental int/coordinate parse — is what resolves it).
  3. Negative check: reconstruct what the ORIGINAL (rejected) plan version would have produced —
     an `ObjectiveState` with `target_position=None` — and assert
     `_resolve_target_position(state, that_version)` returns `(None, None, None)`, i.e. explicitly
     demonstrate the "stalls forever" failure mode the fix prevents, so this test fails loudly if
     a future edit accidentally drops the `target_pos` synthesis and silently regresses to it.
  This test directly satisfies the reviewer's explicit requirement: "not just that `target_id` is
  non-`None`, but that the resulting committed project can actually be tactically resolved."

**Do NOT touch:** `tests/unit/strategic/test_score_normalization.py` — this new file is
deliberately separate (test_plan.md's own judgment call: `test_score_normalization.py`'s scope is
strictly `evaluate_project_switch()`'s lock-bypass normalization, not materialization). **Do not
modify `src/engine/tactical.py`** to make `test_form_party_materialized_objective_is_tactically_
resolvable_not_a_stall` pass — that test must exercise `_resolve_target_position()` completely
unmodified; if it fails, the bug is in Step 2's `target_pos` synthesis, not in `tactical.py`.

**Verify:** `pytest tests/unit/strategic/test_adventure_route_materialization.py -v` passes.

---

### Step 7 — Run the full scoped regression suite

**Files:** none (verification-only step)

**Change:** Run exactly the command test_plan.md specifies:
```
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v
```
All tests must pass, including the full pre-existing regression surface
(`test_phase3_adventure_decision_service.py`, `test_phase3_adventure_decision_boundary.py`,
`test_phase3_adventure_decision_phase.py`) proving `decide()`/`generate()`/`AdventureDecisionPhase`
were not disturbed.

**Do NOT touch:** Never run `pytest tests/` (full suite) per project testing rules.

**Verify:** All listed suites green; no test in the regression surface required an edit to pass
(if one did, that is itself a signal of unintended scope creep into `phase.py`/`service.py`/
`generator.py`/`mapper.py` and must be investigated before Finalize, not silently patched).

## Scope Guards

Mirrors investigation.md's Anti-Drift Hazards verbatim, restated as hard guards:

- Do not modify `src/domains/adventure/phase.py`. `AdventureDecisionPhase` stays fully active and
  wired. Import `_supports_adventure_routing` (and, transitively, `_resolve_cognition_profile_id`)
  from it — do not move or duplicate them.
- Do not touch `src/engine/pipeline.py`. `AdventureGoalScorer` is registered but never wired into
  the pipeline in this ticket (C3's job, gated on this ticket + C4).
- Do not implement `_threat_resolved()` relocation or add a `state` parameter to
  `evaluate_project_switch()` (C2's job). Step 4's new branch fits within
  `evaluate_project_switch()`'s existing `(entity, candidate_project, current_tick)` signature
  unchanged.
- Do not build a shadow-mode comparison test or wire a SimQ pre-cutover gate (C4's job).
- Do not use `best_candidate.utility` anywhere in Step 4's `map_to_states(score=...)` argument —
  the single highest-value regression this ticket must not introduce.
- Do not resolve Risk #1 (target/target_pos gap) by weakening the shared tier-5 floor check at
  `intelligence.py:1373` — that check is shared by all 11 scorers. Step 2's placeholder
  `target_id`/`target_pos` construction (`_resolve_placeholder_target_pos()`) is the only
  sanctioned fix location.
- **Do not resolve Risk #1 by synthesizing `target_id` alone and leaving `target_pos=None`.**
  This was the plan's original approach and was rejected by an architecture-reviewer pass
  (2026-08-11): it clears the target-presence gate but produces a committed project that can
  never make tactical progress (traced through `TacticalDecisionSystem._resolve_target_position()`
  and the `if target_pos:` guards in `tactical.py`). `target_pos` must always be a real,
  resolvable position for these 3 families — never `None`, never a synthetic/placeholder
  coordinate unrelated to real entity/state data.
- Do not touch `src/engine/tactical.py` to "make room" for the Risk #1 fix. The fix supplies real
  data to `_resolve_target_position()`'s existing, unmodified `target_position` fallback
  (`tactical_contract.md` §7) — it does not add a new resolution path or change existing ones.
- Do not change `RouteFamily`, `RouteToProjectMapper._MAP`, or any of the 15 mapped
  `(ProjectKind, ObjectiveKind)` pairs. `RouteToProjectMapper` is wrapped unchanged.
- Do not attempt to close `STRAT-185`'s null `test_path` as a requirement — opportunistic only,
  and no test written in this plan happens to exercise its `text` claim directly, so leave it
  untouched.
- Do not add `AdventureGoalScorer`'s logic into `src/ai/goals/scorers.py` — it lives in its own
  new module (Step 2).
- Do not edit `tests/unit/strategic/test_score_normalization.py`, `test_expanded_goals.py`, or
  `test_enum_drift.py` to "make room" for the new scorer — they must pass unmodified.
- Do not add a `docs/guidelines/intentional_divergences.md` entry for the Risk #1 resolution —
  that entry is only required under Option (b) (accept-as-unwinnable), which this plan did not
  choose. Synthesizing a placeholder `target_id` paired with a real `target_pos` does not diverge
  from any documented Mechanics Bible law; it is new integration behavior for a route family that
  never previously participated in tier-5 arbitration at all, and it follows the existing,
  documented `TacticalDecisionSystem._resolve_target_position()` fallback contract
  (`tactical_contract.md` §7) rather than diverging from it.
- Do not modify `SpatialQueryService.nearest_building()` (`src/engine/spatial_query.py`) —
  `_resolve_placeholder_target_pos()` (Step 2) calls it read-only, matching `RecoverScorer`'s
  existing call pattern exactly.

## Dependency Map

- Step 1 (enum member) has no dependencies. Must land before Steps 2, 3, 4 (all reference
  `GoalKind.ADVENTURE_ROUTE`).
- Step 2 (scorer class) depends on Step 1. Must land before Step 3 (registration imports the
  class) and before Step 4 can be meaningfully tested end-to-end (Step 4's branch reads
  `metadata["route_family"]`/`metadata["raw_score"]`, whose shape Step 2 defines).
- Step 3 (registration) depends on Step 2.
- Step 4 (materialization branch) depends on Step 1 and Step 2's `metadata` key names
  (`"route_family"`, `"raw_score"`) — not on Step 3 (Step 4's code path is reachable via direct
  `evaluate_strategic_intent()` calls in tests even before registration, though Step 6's
  integration tests are more naturally written after Step 3 lands so `GoalRegistry` picks up the
  scorer automatically).
- Step 5 (unit tests) depends on Steps 1-3 (needs the enum member, the scorer class, and — for
  the registry-membership assertions — registration).
- Step 6 (integration tests) depends on Steps 1-4 (exercises the full tier-5-win →
  materialization path end-to-end). Its new
  `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall` test additionally
  depends on Step 2's `_resolve_placeholder_target_pos()` (the source of the real `target_pos` it
  asserts on) and reads `TacticalDecisionSystem._resolve_target_position()`
  (`src/engine/tactical.py`, unmodified by this plan — a read-only dependency, not a step this
  plan implements).
- Step 7 (regression run) depends on Steps 1-6 all landing.

No step depends on any ticket explicitly marked Out of Scope (C2/C3/C4).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `GoalKind.ADVENTURE_ROUTE` new member; `AdventureGoalScorer` implements `GoalScorer.score()`; registered via `GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer())` in `__init__.py` | Step 1, Step 2, Step 3 | `test_goal_kind_adventure_route_is_registered_member`, `test_adventure_goal_scorer_implements_goal_scorer_protocol` |
| AC2 — `score()` calls `decide()` unchanged; returns `GoalScore(kind=..., utility=(raw_score/_ADVENTURE_ROUTE_SCORE_MAX)*_GOAL_UTILITY_SCORE_MAX, metadata={"route_family":...,"raw_score":raw_score,...})`; `raw_score=2.9 -> utility==100.0` exactly | Step 2 | `test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact`, `test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score` |
| AC3 — materialization branch calls `RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...)`, never `best_candidate.utility`, across all 15 mapped families, preserving `(None, None)` handling for `DEFER_WITH_REASON` | Step 4 | `test_adventure_route_winner_materializes_with_raw_score_not_utility`, `test_adventure_route_winner_preserves_none_none_handling_for_defer_family` |
| AC4 — dedicated regression test asserts materialized `ADVENTURE_ROUTE` winner's `ProjectState.score` equals `metadata["raw_score"]`, never `best_candidate.utility` | Step 4, Step 6 | `test_adventure_route_winner_materializes_with_raw_score_not_utility` |
| AC5 — ineligible entities and `DEFER_WITH_REASON` produce `GoalScore(utility=0, target_id=None)` that never clears the 20.0 tier-5 floor | Step 2 | `test_adventure_goal_scorer_ineligible_entity_returns_zero_utility_no_target`, `test_adventure_goal_scorer_defer_with_reason_returns_zero_utility_no_target` |
| AC6 — deliberate (not arbitrary) tie-break string value for `GoalKind.ADVENTURE_ROUTE` | Step 1 (`"z_adventure_route"`, justified in "Unresolved Questions Now Resolved") | `test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds`, `test_adventure_route_loses_exact_utility_tie_against_existing_kind` |

**AC5 cross-check (Fact-Verification Requirement #3, re-confirmed after this revision):** AC5's
`GoalScore(utility=0, target_id=None)` field names and values are produced verbatim only by the
`ineligible`/`DEFER_WITH_REASON` early-return paths in Step 2's `score()` — those two paths are
unchanged by this revision (still `GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=0.0,
target_id=None, ...)`, no `target_pos` set, defaulting to `None` per `GoalScore`'s own dataclass
default at `src/ai/goals/base.py:8-14`). The Risk #1 `target_pos` synthesis added in this revision
only executes in the **separate**, non-ineligible/non-`DEFER_WITH_REASON` branch (forced
`RECOVER`/`ASK_INFORMATION`/`FORM_PARTY` with a real winning route), so it does not alter what AC5
itself asserts. No contradiction between AC5's stated fields/values and this plan's Steps.

## Anti-Drift Notes

- **Risk #1's "wins but stalls" hazard (added by this plan revision, 2026-08-11 architecture-
  reviewer pass) — the second highest-value regression to guard, alongside the raw-score one
  below**: Step 2's `_resolve_placeholder_target_pos()` must always return a real, non-`None`
  position for `RouteFamily.RECOVER`/`ASK_INFORMATION`/`FORM_PARTY` when reached (never `None`,
  never a value structurally incapable of being resolved by
  `TacticalDecisionSystem._resolve_target_position()`'s `target_position` fallback). A regression
  back to `target_pos=None` for these 3 families would silently reintroduce the exact defect the
  architecture-reviewer traced end-to-end: the candidate still wins tier-5 arbitration and locks
  the project slot (nothing about the floor-gate check changes), but the entity never starts
  navigating and the project can never resolve — a *silent* stall, not a crash, exactly the kind
  of regression that is easy to miss without
  `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall` (Step 6)
  specifically asserting on `_resolve_target_position()`'s return value, not just on `target_id`.
- **`_resolve_placeholder_target_pos()`'s data sources are deliberately borrowed, not invented**:
  `RECOVER` mirrors `RecoverScorer`'s own nearest-inn/town_center fallback
  (`scorers.py:181-186`), `ASK_INFORMATION` mirrors `TownScorer`'s `state.town_center`
  (`scorers.py:98`), `FORM_PARTY` mirrors `generator.py`'s own FORM_PARTY candidate-eligibility
  filter (`generator.py:126-137`). Do not "simplify" any of these to a synthetic/arbitrary
  coordinate (e.g. `(0.0, 0.0)`, `entity.navigation.position` for all three uniformly, etc.)
  during Implement — each family's source was chosen to match an existing, working precedent in
  this codebase, not picked arbitrarily.
- **`node_id`/`building_id` staying `None` for these 3 families after the fix is expected,
  documented, accepted behavior — not a residual bug.** `docs/engine/contracts/
  tactical_contract.md` §7 already documents this exact limitation for `TownScorer`'s own
  `"town_center"`-targeted winners: "objective resolved only via the `target_position` fallback
  still navigates to the position, but arrival dispatches to a bare idle `EntityUpdate` rather
  than INTERACT/EAT/REST." Do not attempt to give these 3 families a real `node_id`/`building_id`
  or extend arrival-dispatch for them (mirroring `GUILD`'s dedicated `GuildVisitPhase`) — that is
  explicitly out of scope per `tactical_contract.md` §7's own closing paragraph ("a separate,
  not-yet-filed follow-up").
- **The single highest-value regression to guard**: Step 4's `map_to_states(score=...)` argument
  must be `best_candidate.metadata.get("raw_score", 0.0)`, never `best_candidate.utility`. A
  regression here silently reproduces the just-fixed
  `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` defect class — the entity still
  "works," it just becomes permanently un-interruptible or trivially-interruptible depending on
  which direction the scale mismatch goes (design doc Sec 4).
- **Circular-import ordering hazard (new finding, not in investigation.md)**: Step 2's imports of
  `intelligence.py`'s `_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX` constants MUST stay
  function-local inside `score()`. `intelligence.py:77`'s top-level
  `from src.ai.goals import GoalRegistry` means `src.ai.goals` and
  `src.systems.strategic_systems.intelligence` can each trigger the other's module load as a
  nested side effect once `adventure_scorer.py` is registered in `__init__.py`. A top-level
  import of the constants in `adventure_scorer.py` would only work if `GoalRegistry` happens to
  already be bound in `src.ai.goals`'s partially-initialized namespace by the time
  `intelligence.py`'s own import line executes — true today only because `__init__.py`'s existing
  `from src.ai.goals.base import GoalRegistry` line already precedes where Step 3 adds the new
  `AdventureGoalScorer` import — but this is exactly the kind of fragile, easy-to-silently-break
  ordering dependency the lazy-import pattern avoids entirely. Do not "simplify" this to a
  top-level import during Implement even if it happens to work when first tested. **Correction
  (2026-08-11, Finding 2 from the architecture-reviewer pass)**: an earlier version of Step 2's
  inline comment claimed "phase.py has no import path back to `src.ai.goals` or
  `src.systems.strategic_systems`" — this was factually wrong and has been struck from Step 2's
  code block. A transitive path DOES exist and was confirmed by reading the files directly:
  `phase.py:20` → `from src.systems.strategic import StrategicIntelligenceSystem`; `src/systems/
  strategic.py` is a one-line shim → `from src.systems.strategic_systems.intelligence import
  StrategicIntelligenceSystem`; `intelligence.py:77` → `from src.ai.goals import GoalRegistry`.
  The plan's actual mitigation (both the `_supports_adventure_routing` import and the constants
  import staying function-local/lazy) was already sound and needs no further change — only the
  comment's factual claim was wrong, not the design. Implement must write the corrected comment
  exactly as it now appears in Step 2's code block (crediting the lazy-import pattern for keeping
  the *real* transitive path safe, not claiming the path doesn't exist).
- **`existing`/resume-suspended-project branch (`intelligence.py:1390-1399`) is a known,
  accepted no-op for `ADVENTURE_ROUTE` winners** — see Step 4's "Do NOT touch" note. Do not
  "fix" this to make adventure projects resumable from suspension; that is new behavior outside
  this ticket's scope.
- **`faction_directives=None` in Step 2's `decide()` call is a disclosed simplification**, not an
  oversight — there is no `state.faction_directives` attribute (confirmed: `AuthoritativeState`
  has `resource_nodes` at `state.py:1096` and `factions` at `state.py:1156`, but no
  `faction_directives` field; that value is a pipeline-level artifact computed by
  `FactionDecisionPhase.execute()` at `pipeline.py:181`, not state). Do not attempt to thread real
  faction directives through in this ticket — C3 (the wiring ticket) owns that decision once this
  scorer is actually live in the pipeline.
- **Docs**: `docs/mechanics/04_strategic_cognition.md` §2/§6.6 and
  `docs/parity_ledger/strategic_cognition.yaml` (STRAT-185/186/187 opportunistically,
  STRAT-236 explicitly NOT touched) are flagged for update by the Docs/Parity phases per
  investigation.md's "Docs Requiring Update" section — not spelled out as Implement steps here
  since those are separate downstream pipeline phases (doc-updater/parity-updater), but must not
  be silently skipped when those phases run.
