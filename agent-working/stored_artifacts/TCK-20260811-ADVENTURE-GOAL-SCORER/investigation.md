---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-ADVENTURE-GOAL-SCORER
artifact_type: investigation
tags: [cognition, adventure]
---

# Investigation — TCK-20260811-ADVENTURE-GOAL-SCORER

## Current Behavior

### `src/ai/goals/base.py` (whole file, 52 lines)
- `GoalScore` (frozen dataclass, lines 8-14): `kind: GoalKind | str`, `utility: float`, `target_id: Optional[str] = None`, `target_pos: Optional[tuple[float,float]] = None`, `metadata: Dict[str, Any] = field(default_factory=dict)`. `metadata` exists today but **no scorer in `scorers.py` currently populates it** — this ticket is the first real consumer.
- `GoalScorer` (Protocol, lines 16-19): `score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore`.
- `GoalRegistry.register()` (lines 25-43): validates `kind` via `GoalKind(kind)` (raises `ValueError` if not a real member/value) — confirms `GoalKind.ADVENTURE_ROUTE` must exist as a real enum member before registration will succeed. Also raises on class-conflict re-registration (idempotent-safe for the same class).
- `GoalRegistry.get_all_scores()` (lines 45-50): iterates `sorted(cls._scorers.keys())` — a **different** sort from the tier-5 arbitration sort in `intelligence.py`; this one only fixes call order (deterministic across ticks), not selection.

### `src/ai/goals/scorers.py` (260 lines) — existing scorer patterns
10 scorer classes exist (`HarvestScorer`, `SleepScorer`, `EatScorer`, `SocialScorer`, `TownScorer`, `CombatEngageScorer`, `CombatRetreatScorer`, `RecoverScorer`, `ResolveBlockerScorer`, `GuildNeedScorer`). Common shape: read `entity`/`state`, compute a float `utility`, return `GoalScore(kind=GoalKind.X, utility=..., target_id=..., target_pos=...)`. None populate `metadata`. `GuildNeedScorer` (lines 228-258) is the most recently added and the closest structural precedent for gating behind eligibility checks (feature flag + capacity check) before computing a real score — `AdventureGoalScorer` should mirror this "early-return unwinnable `GoalScore`" shape for the ineligible/defer paths.

### `src/ai/goals/__init__.py` (21 lines) — registration site
`GoalRegistry.register(GoalKind.X, XScorer())` calls, one per line, imported from `scorers.py`. `AdventureGoalScorer` will live in a **new** module (design doc §5: "co-locate with the other scorers in `src/ai/goals/`" — a new file, not `scorers.py` itself, since it needs the adventure-domain imports `AdventureDecisionService`, `AdventureRouteGenerator`, opportunity providers, and the relocated eligibility helpers; keeping those imports out of `scorers.py` avoids giving every other scorer a transitive import surface into `src/domains/adventure/`). Recommend `src/ai/goals/adventure_scorer.py`, imported and registered in `__init__.py` the same way.

### `src/core/strategic.py:121-133` — `GoalKind` enum (exact current membership)
```python
class GoalKind(str, Enum):
    """Types of strategic goals/scorers."""
    HARVESTING = "harvesting"
    FATIGUE = "fatigue"
    HUNGER = "hunger"
    SOCIAL = "social"
    TOWN_RETURN = "town_return"
    COMBAT_ENGAGE = "combat_engage"
    COMBAT_RETREAT = "combat_retreat"
    RECOVER = "recover"
    RESOLVE_BLOCKER = "resolve_blocker"
    GUILD = "guild"
```
10 members today. `ADVENTURE_ROUTE` is a new 11th member. Because `GoalKind(str, Enum)`, its **string value** is what participates in `<` comparisons during tie-break sort (see below) — the enum identity is also what `_score_scale_max()` (`intelligence.py:89-107`) uses via `isinstance(kind, ProjectKind)` to classify System A vs System B (a `GoalKind` member, including `ADVENTURE_ROUTE`, is **never** `isinstance(..., ProjectKind)`, so `AdventureGoalScorer`'s `GoalScore.utility` is correctly classified onto the `_GOAL_UTILITY_SCORE_MAX` (100.0) scale for tier-5 competition — this is exactly why normalization in §3 is required before the `GoalScore` is built).

### `src/domains/adventure/service.py` — `AdventureDecisionService.decide()` (confirmed exact signature)
```python
@staticmethod
def decide(
    entity: EntityState,
    candidates: List[AdventureRouteOption],
    tick: int = 0,
    resource_nodes: Optional[Dict[int, ResourceNodeState]] = None,
    faction_directives: Optional[list] = None,
    factions: Optional[Any] = None,
) -> AdventureDecisionResult:
```
**Critical correction to the design doc's phrasing** ("wraps `AdventureDecisionService.decide()` — completely unchanged: still generates up to 25 candidates via `AdventureRouteGenerator`"): `decide()` itself does **not** call `AdventureRouteGenerator` — it takes `candidates` as a required positional parameter. Candidate generation (`AdventureRouteGenerator.generate(hero, state, opportunities=...)`, `generator.py:24-29`) and opportunity assembly (`ResourceOpportunityProvider.get_opportunities()` + `ServiceOpportunityProvider.get_opportunities()`, currently only called from `phase.py:155-158`) happen **before** `decide()` is called. `AdventureGoalScorer.score()` must replicate all three calls (opportunities → generate → decide), not just call `decide()` alone — this is a materially larger `score()` body than "just wrap decide()" might suggest, though every one of the three calls is itself unchanged.

`decide()` internally already calls `RouteToProjectMapper.map_to_states(family=selected.family, entity_id=entity.id, target=target, target_pos=target_pos, tick=tick, score=selected.score)` (service.py:141-148) using the **raw** `selected.score` — this pre-built `result.proposed_project`/`result.proposed_objective` pair already has the correct raw-scored `ProjectState`. `AdventureGoalScorer` does **not** need this pre-built pair for the `GoalScore` itself (only `utility`, `target_id`, `target_pos`, and `metadata` are needed) — but it is a convenient source for `target_id`/`target_pos`/`objective_kind` since the mapping logic (`RouteToProjectMapper.get_kinds`) doesn't need to be re-run to source `objective_kind`. See "Concrete `AdventureGoalScorer.score()` design" below for why this pre-built pair must **not** be reused wholesale for materialization.

`decide([])` (empty candidates) returns a `DEFER_WITH_REASON` result (lines 52-68) — this path is reachable if opportunity assembly + generation yields nothing, in addition to `generate()`'s own internal empty-fallback (see below, `generator.py:165-176`, which itself also falls back to `DEFER_WITH_REASON` if `opts` is empty after all rules run — so in practice `candidates` passed to `decide()` is rarely truly `[]`, but `decide()` still handles it defensively).

### `src/domains/adventure/generator.py` — `AdventureRouteGenerator.generate()` (confirmed signature + target-population gap)
```python
@staticmethod
def generate(entity: EntityState, state: Any = None, opportunities: Sequence[Opportunity] = ()) -> Tuple[AdventureRouteOption, ...]:
```
Capped to 25 (`generator.py:179`, `opts[:25]`). **Confirmed structural gap, directly relevant to AC5 ("never clears the 20.0 tier-5 floor" framing) and materialization correctness**: three of the generated route shapes never populate `target_node_id` or `source_opportunity_ids`:
- The forced `RECOVER` route (lines 98-109, triggered by `perceived_weaknesses`/`healing` need, independent of any opportunity)
- The forced `ASK_INFORMATION` route (lines 111-123, triggered by `weak_weapon`/`equipment_improvement` need)
- The `FORM_PARTY` route (lines 125-163) — **always** structural, no `kind_map` entry ever produces it from an opportunity, so it **always** lacks `target_node_id`/`source_opportunity_ids`.

In `service.py:133-140`, `target` is derived only from `selected.target_node_id` or `selected.source_opportunity_ids[0]` — **`target_pos` is never set at all in `decide()`, it stays `None` unconditionally** (service.py:135, never reassigned). So for any of the three route shapes above, `result.proposed_objective.target` is `None` **and** `target_position` is always `None` regardless of route shape. See "Risks and Open Questions" — this directly threatens the tier-5 floor gate at `intelligence.py:1373`.

### `src/domains/adventure/mapper.py` — `RouteToProjectMapper` (confirmed exact contents)
`_MAP` (lines 31-47) has **15 entries**, one per `RouteFamily` member except `DEFER_WITH_REASON`. `RouteFamily` (`schema.py:16-33`) has **16 members total** (confirmed by direct enumeration): `RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, TRAIN_SKILL, TAKE_EASY_QUEST, HUNT_WEAK_ENEMY, GATHER_RESOURCE, SELL_LOOT_FOR_GOLD, ASK_INFORMATION, SCOUT_LOCATION, FORM_PARTY, RETURN_TOWN, DEFER_WITH_REASON, QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL`. `get_kinds()` (lines 49-64) returns `(None, None)` specifically for `RouteFamily.DEFER_WITH_REASON`; `map_to_states()` (lines 66-108) propagates that `(None, None)` straight through as its own return value (line 81-82: `if p_kind is None or o_kind is None: return None, None`) — this is the exact "DEFER_WITH_REASON None-handling" the ticket's Assumptions section calls out, and it is already correctly structured for the materialization branch to reuse (`if proj is None or obj is None: <no-op path>`).

`map_to_states()` signature (confirmed):
```python
@classmethod
def map_to_states(self, family: RouteFamily, entity_id: int, target: Optional[str] = None,
                   target_pos: Optional[Tuple[float, float]] = None, tick: int = 0,
                   score: float = 1.0) -> Tuple[Optional[ProjectState], Optional[ObjectiveState]]:
```
(Note: first parameter is literally named `self` despite being a `@classmethod` — a pre-existing naming quirk, harmless since Python binds the class to whatever the first positional parameter is named; not something to "fix" in this ticket, out of scope.)

### `src/domains/adventure/schema.py` — `RouteFamily` (confirmed 16 members) and `AdventureRouteOption`
Confirmed as summarized above. `AdventureRouteOption.score: float` is the field the ticket/design doc call "raw_score" — this is literally `route.score` after `AdventureRouteScorer.score()` has run (0.0-~2.9 range, `04_strategic_cognition.md` §6.6).

### `src/domains/adventure/scoring.py` — `AdventureRouteScorer.score()` (unchanged by this ticket, confirmed formula)
`final_score = urgency + benefit + personality_bias + plan_advance_bonus + confidence_bonus - risk_penalty - blocker_penalty`, clamped `max(0.0, ...)`, then class-synergy/escort multipliers applied. This is the ~0-2.9 raw scale cited throughout the design doc and mechanics doc §6.6. Not touched by this ticket.

### `src/domains/adventure/phase.py` — `AdventureDecisionPhase`, `_threat_resolved()`, `_resolve_cognition_profile_id()`, `_supports_adventure_routing()` (confirmed exact contents; **not modified by this ticket**, out-of-scope, read for situational awareness only)
- `_threat_resolved(hero, state)` (lines 27-46): HP>80% AND no hostile within radius 10.0. Explicitly out of scope (THREAT-RESOLVED-ARBITER-RELOCATION / C2's job).
- `_resolve_cognition_profile_id(entity)` (lines 49-80) and `_supports_adventure_routing(entity, cache)` (lines 83-96): the 3-tier eligibility resolution landed by `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY`. `_supports_adventure_routing` takes a `cache: Dict[str, bool]` that `phase.py` currently constructs fresh **once per `AdventureDecisionPhase.apply()` call** (line 126, shared across the loop of all heroes evaluated that tick) — a performance optimization (look up the catalog once per distinct profile id, not once per hero).
- `AdventureDecisionPhase.apply()` (lines 104-220): the full current per-hero flow this ticket's `AdventureGoalScorer.score()` must replicate for a *single* entity: lock-check skip (146-152, **not** replicated — tier-5 competition happens only when tiers 1-4 didn't already act, so the equivalent "is there an active locked project" concern is handled upstream by `evaluate_strategic_intent`'s own tiers, not by the scorer itself) → opportunities (155-158) → `AdventureRouteGenerator.generate()` (159) → `AdventureDecisionService.decide()` (162-167) → (trace-write, DEFER handling, materialization). Only the opportunities → generate → decide sequence needs replicating inside `score()`; the DEFER handling and materialization are handled differently (via `GoalScore` shape and the new `intelligence.py` branch, respectively) per this design.
- `AdventureDecisionPhase` itself, and its `pipeline.py:237-244` registration, are **confirmed still active and unmodified** — `pipeline.py:237` imports `AdventureDecisionPhase` and registers it as the `"adventure_decision"` phase, unconditionally, with no feature-flag gate visible at this call site. This ticket must not touch `pipeline.py` (ticket Out of Scope, C3's job) or `phase.py` (not listed in ticket Scope at all — see Anti-Drift Hazards).

### `src/systems/strategic_systems/intelligence.py` (1461 lines total) — tier-5 call site and materialization branch (confirmed exact current line numbers; this file was modified once already this session, so the design doc's own line citations were re-verified directly rather than trusted)
Constants (module level):
```python
32: _ADVENTURE_ROUTE_SCORE_MAX: float = 2.9
47: _GOAL_UTILITY_SCORE_MAX: float = 100.0
53: _INTERRUPTION_URGENCY_FLOOR_PCT: float = 0.8
```
`_score_scale_max()` (lines 89-107): classifies by **enum class identity** (`isinstance(kind, ProjectKind)` → `_ADVENTURE_ROUTE_SCORE_MAX`; else → `_GOAL_UTILITY_SCORE_MAX`). A `GoalKind.ADVENTURE_ROUTE`-kinded `GoalScore.utility` is therefore always classified onto the 100.0 scale (correct — it's a System B/`GoalRegistry` candidate at the scoring stage, even though its winning materialized `ProjectState.kind` becomes a real `ProjectKind` afterward).

`evaluate_project_switch()` signature (lines 928-933, confirmed, **no `state` parameter today** — matches design doc §5's finding, out of scope to change here):
```python
@staticmethod
def evaluate_project_switch(entity: EntityState, candidate_project: ProjectState, current_tick: int) -> Optional[StrategicUpdate]:
```

Tier-5 call site and arbitration (confirmed exact lines):
```python
1355: all_scores = GoalRegistry.get_all_scores(entity, state)
1358-1363: # PH9 routine/role utility boost per score, via s.kind.lower()
1366: all_scores = PartyCoordinationSystem.apply_leadership_influence(entity, state, all_scores)
1368: modified_scores = ScoreModifierSystem.apply_modifiers(entity, state, all_scores)
1369: modified_scores.sort(key=lambda x: (-x.utility, x.kind))
1371-1376: best_candidate = first g_score where utility >= 20.0 AND (target_id or target_pos) is not None
```
Confirmed: `s.kind.lower()` (line 1360-1361, passed into `RoutineService.get_routine_utility_boost`/`get_role_utility_boost`, `src/systems/world_systems/routine.py:102,130`) works fine for an unrecognized kind string like `"adventure_route"` — both functions do plain `==`/`.upper()==` comparisons against known literals and fall through to `0.0`/no boost for anything unmatched (verified: `routine.py:112` `if project_kind == "sleep"`, `routine.py:138-145` explicit role/kind pairs) — no special-casing needed, no risk of an exception.

**Materialization branch (confirmed exact current lines, generic-only today — no `ADVENTURE_ROUTE` special case exists yet)**:
```python
1389: if best_candidate:
1390:     existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)
1392-1399:     if existing and existing.status == ProjectStatus.SUSPENDED:  # resume path, unrelated
1401:     cand_kind_str = getattr(best_candidate.kind, "value", best_candidate.kind)
1402-1408:     obj = ObjectiveState(id=f"{cand_kind_str}_{best_candidate.target_id}", kind="reach_location",
                    target=best_candidate.target_id, target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE)
1409-1418:     candidate_proj = ProjectState(id=f"proj_{cand_kind_str}_{current_tick}", kind=best_candidate.kind,
                    status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id,
                    lock_until_tick=min(current_tick+10, current_tick+50), created_tick=current_tick,
                    score=best_candidate.utility)
1420-1424: at_capacity check
1426: switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick)
```
(Design doc §4 cited "approximately lines 1397-1414" for this construction; re-verified directly here: the real generic construction is lines 1401-1418, with the `if best_candidate:` guard opening at 1389 and the existing-suspended-project short-circuit occupying 1390-1399 in between. Cite the re-verified numbers, not the design doc's approximation, in `plan.md`.)

This confirms the design doc's §4 bug analysis exactly: line 1417 (`score=best_candidate.utility`) is the generic path's score assignment — for a non-`ADVENTURE_ROUTE` winner this is correct (a `GoalKind`-typed `ProjectState` is later classified by `_score_scale_max()` onto the 100.0 scale, matching `utility`'s own normalization basis). For an `ADVENTURE_ROUTE` winner materialized through `RouteToProjectMapper`, `ProjectState.kind` becomes a real `ProjectKind` member — classified onto the 2.9 scale by `_score_scale_max()` — so reusing this same `score=best_candidate.utility` line for that branch would put a 100-scale number into a project whose own scale is later read as 2.9-max, exactly the defect class described in design doc §4 and shared with `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`.

### `src/engine/pipeline.py:237-244` (confirmed, situational awareness only, not touched)
```python
237: from src.domains.adventure.phase import AdventureDecisionPhase
238-244: update = run_phase("adventure_decision", update,
              lambda u: u.merge(AdventureDecisionPhase.apply(state, faction_directives=faction_directives, factions=state.factions)))
```
Confirmed still active, unconditional, no flag gate at this call site. This ticket must not change this file (Out of Scope, C3's job, gated on this ticket + C4 landing first).

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md` §2 ("Generalized Bypass")**: governs `evaluate_project_switch()`'s lock-bypass gate — the normalized-percentage-of-own-declared-max pattern this ticket's §3 normalization directly reuses (per design doc, "the exact same two constants already introduced for that gate"). Any `ADVENTURE_ROUTE`-kinded candidate competing for a locked slot goes through this unchanged law; this ticket doesn't touch it, only supplies correctly-scaled inputs to it.
- **`docs/mechanics/04_strategic_cognition.md` §6.6 ("Score Range Summary")**: the authoritative source for the `~2.9` ceiling (`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, cited directly in the doc at `04_strategic_cognition.md:257-259` as "the normalization anchor... that System A candidate scores are divided by"). This ticket's §3 normalization (`utility = (raw_score/_ADVENTURE_ROUTE_SCORE_MAX)*_GOAL_UTILITY_SCORE_MAX`) is a **new consumer** of this same anchor value, for a different purpose (goal-competition normalization, not lock-bypass normalization) — both readings must stay consistent if `_ADVENTURE_ROUTE_SCORE_MAX` is ever recalibrated.
- **`docs/mechanics/adventure_routing_contract.md`** (companion to `04_strategic_cognition.md`, surfaced by `search_docs` for this ticket's topic): documents the RouteFamily taxonomy and existing routing contract. Should be checked by Implement for any language describing `AdventureDecisionPhase` as *the* routing mechanism — if so, it needs updating once the goal-scorer path exists as an alternative entry point (even while `AdventureDecisionPhase` is still the only *wired* path in this ticket, the doc's description of "how adventure decisions get made" is now incomplete once `AdventureGoalScorer` exists as unit-testable code, even if unwired).
- **Durable State Rule (CLAUDE.md)**: `GoalScore` itself is not durable state — it's an intra-tick computation handoff, never persisted, never surviving beyond `evaluate_strategic_intent()`'s own call. Storing `route_family`/`raw_score`/`objective_kind` in `GoalScore.metadata` (a `Dict[str, Any]`) is therefore consistent with the Durable State Rule's actual scope (it constrains what survives beyond the current tick/function call — `metadata` here is consumed and discarded within the same `evaluate_strategic_intent()` call that produced it). The rule *does* apply to what gets committed into `ProjectState`/`ObjectiveState` (a real `StateUpdate`) — which is exactly why §4's raw-score-not-utility distinction matters: the committed `ProjectState.score` is durable and must be on the correct scale.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §2's goal-hierarchy description and §6.6's normalization-anchor note both currently describe `AdventureDecisionPhase` as running as a separate, earlier pipeline phase invisible to tiers 1-4 (matching current reality). Once `AdventureGoalScorer` exists as a new, unit-testable tier-5 candidate (even while unwired from `pipeline.py`), a short addition is needed noting the new component exists and where it fits, to avoid the doc going stale the moment it's implemented — full "AdventureDecisionPhase deleted, tier-5 wired" language is deferred until the wiring ticket (C3), but silently leaving a whole new scorer undocumented for however long C2-C4 take to land is itself a doc-parity gap.
- `docs/parity_ledger/strategic_cognition.yaml`: `STRAT-236`'s `text` field (lines 2696-2706) currently says "the lock is bypassed in `AdventureDecisionPhase`" — this ticket doesn't relocate `_threat_resolved()` (that's explicitly out of scope, C2's job per design doc §5's "Resolved" note), so `STRAT-236` itself should **not** be touched by this ticket; flagging here only so Implement doesn't accidentally scope-creep into it. `STRAT-185`/`STRAT-186`/`STRAT-187` (`:1987-2024`) already exist and are `P0`/`verified`; `STRAT-185` still has `test_path: null` — closing it is a disclosed **opportunity**, not a requirement, per the ticket's own Assumptions section; if a new test happens to exercise "strategic project retention is bounded by interruption resistance" for the `ADVENTURE_ROUTE` case specifically, update `STRAT-185.test_path` in the same session, but do not force a test into existence purely to close this entry.

## Parity Ledger Overlap

- **STRAT-185** (P0, `strategic_cognition.yaml:1987-1996`): "Strategic project retention is bounded by interruption resistance." `test_path: null` today — a pre-existing gap, opportunistically closeable but not required by this ticket's scope.
- **STRAT-186** (P0, `:1997-2011`, `verified`, `test_path: tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`): "Strategic project switching requires margin or explicit emergency." Directly exercised by any `ADVENTURE_ROUTE`-kinded candidate that later becomes `current` and needs interrupting — this ticket's correctness (raw_score threading) is a precondition for STRAT-186 continuing to hold once adventure routes through the shared gate, but this ticket does not change STRAT-186's own mechanism.
- **STRAT-187** (P0, `:2012-2024`, `verified`, same `test_path` file, different test): "Current project has reservation priority." Same relationship as STRAT-186.
- **STRAT-236** (P1, `:2696-2711`, `verified`, `test_path` unclear from excerpt — check before Implement): describes the `_threat_resolved()` early-release mechanic, currently `AdventureDecisionPhase`-specific in its `text` field. Not touched by this ticket (C2's job); flagged only to prevent scope creep.
- No `P0` entry in scope for this ticket lacks a `test_path` in a way this ticket is required to fix — STRAT-185's gap is pre-existing and orthogonal.

## Prior Work

- **`TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY`** (done, stored artifacts at `stored_artifacts/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY/`): landed `_resolve_cognition_profile_id`/`_supports_adventure_routing` exactly as they exist in `phase.py` today — the eligibility logic `AdventureGoalScorer.score()` step 1 must reuse (via import, not relocation — see Anti-Drift Hazards).
- **`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`** (done): landed the normalized-percentage-of-own-max lock-bypass pattern (`_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX` constants) this ticket's §3 normalization directly reuses. Also fixed `RouteToProjectMapper.map_to_states()`'s previous hardcoded `score=1.0` placeholder to use real route scores — meaning `map_to_states(score=...)` today already expects and correctly handles a real raw score argument, exactly what this ticket's materialization branch must supply.
- **`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`** (done, most recent): fixed the `retention_margin` normalization-denominator bug that this design doc's Non-goals section calls a hard prerequisite — confirmed landed (`intelligence.py:995`, `normalized_effective_current_pct = (current.score / current_max) + (retention_margin / _GOAL_UTILITY_SCORE_MAX)`, dividing by the fixed constant, not `current_max`). This ticket's own §4 raw-score-not-utility fix is described by the design doc as "independently... the same defect class" as this bug — the regression test for §4 should be written with the same discipline (real worked arithmetic, not just an incidental assertion) as `test_score_normalization.py`'s existing tests for that ticket.
- **`TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT`** (tagged `cognition`, touches `src/ai/goals/`): worth a quick check by Implement in case it left any stale references to "10 scorers" or similar counts that this ticket's 11th scorer would invalidate.
- **`tests/unit/strategic/test_expanded_goals.py`** and **`tests/unit/strategic/test_score_normalization.py`**: both read in full; conventions confirmed and mirrored in `test_plan.md`.

## Risks and Open Questions

1. **Target/target_pos gap for structural-fallback route families (confirmed, not speculative)**: `RECOVER` (when forced by `perceived_weaknesses`, not opportunity-backed), `ASK_INFORMATION` (when forced), and `FORM_PARTY` (always) produce `AdventureRouteOption`s with no `target_node_id` and no `source_opportunity_ids`. `decide()` then leaves `target=None` and (unconditionally, for every route) `target_pos=None`. If `AdventureGoalScorer.score()` passes these straight through into `GoalScore(target_id=None, target_pos=None, ...)`, the tier-5 floor gate at `intelligence.py:1373` (`if ... (target_id is None and target_pos is None): continue`) will **always** reject these candidates regardless of utility — meaning an eligible, non-deferred, well-scored `FORM_PARTY` (or forced-`RECOVER`/`ASK_INFORMATION`) winner would silently never win tier 5, contradicting AC5's framing that only "ineligible entities and DEFER_WITH_REASON results" produce an unwinnable score. **This is a real design gap this ticket's implementation must resolve, not silently inherit** — options include synthesizing a non-null placeholder `target_id` (e.g. `f"adventure:{family.value}"`) for these families when `decide()` leaves `target` unset, or confirming via `plan.md`/architecture review that AC5's silent-loss framing should explicitly cover these three families too (i.e., accept that FORM_PARTY/forced-RECOVER/forced-ASK_INFORMATION can never win tier 5 as designed, since `evaluate_strategic_intent`'s target-presence requirement predates this design and applies uniformly). **Flagging as blocking for Plan, not assuming an answer** — this materially changes what "correctly implemented" means for 3 of the 15 mapped families.
2. **`AdventureGoalScorer.score()` must replicate three calls, not one** (opportunities assembly, `AdventureRouteGenerator.generate()`, `AdventureDecisionService.decide()`) — the design doc's "wraps `AdventureDecisionService.decide()` unchanged" phrasing undersells this; all three are individually unchanged, but `score()`'s body is a real ~15-20 line sequence, not a one-line delegate call.
3. **Per-tick profile-eligibility cache lifecycle changes shape**: `phase.py`'s `_supports_adventure_routing(entity, cache)` expects a `cache: Dict[str, bool]` shared across all heroes evaluated in one `apply()` call. `AdventureGoalScorer.score(entity, state)` is invoked once per entity (via `GoalRegistry.get_all_scores(entity, state)`, itself called once per entity per tick from `evaluate_strategic_intent`) — there's no natural per-tick shared cache object available at this call site. A module/class-level cache dict on the new scorer module (persisting across ticks, not just within one call) is a reasonable substitute since cognition profile definitions are static content for the run's duration — flagging as an implementation-detail decision for Plan, not a blocker.
4. **`RouteToProjectMapper.map_to_states()` is called twice per winning tick** under this design: once inside `decide()` (using `tick=tick` at scoring time, discarded — `decide()`'s own `proposed_project`/`proposed_objective` are not used for materialization) and once in the new `intelligence.py` branch (using `current_tick` at materialization time, from `metadata["raw_score"]`/`metadata["route_family"]`). Since both calls happen within the same tick's `evaluate_strategic_intent()` invocation, `tick == current_tick`, so the two calls produce byte-identical `ProjectState`/`ObjectiveState` IDs and content — the duplication is real but harmless (a deterministic pure function called twice with identical inputs), not a correctness risk, just a minor inefficiency Implement may choose to avoid by threading `decide()`'s already-built `proposed_project`/`proposed_objective` through `metadata` instead of raw `route_family`/`raw_score` — **however, doing so would deviate from the ticket's own AC3 wording** ("the new materialization branch calls `RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...)`"), so the double-call approach matching AC3's literal wording is the correct default unless Plan explicitly decides otherwise.
5. **Tie-break string value for `GoalKind.ADVENTURE_ROUTE` — mechanics confirmed, default value flagged as likely wrong direction**: sort is `modified_scores.sort(key=lambda x: (-x.utility, x.kind))` (line 1369), and the winner is the **first** post-sort candidate clearing the floor (loop at 1371-1376 takes the first match, no explicit stable-max search). Since `GoalKind(str, Enum)`, `x.kind` compares as its string value; ascending sort means **the alphabetically-smallest kind value wins ties**. Existing 10 values sorted: `combat_engage, combat_retreat, fatigue, guild, harvesting, hunger, recover, resolve_blocker, social, town_return`. The naturally-descriptive value `"adventure_route"` sorts **before all 10** (since `'a' < 'c'`) — meaning a naive choice would make `ADVENTURE_ROUTE` win *every* exact-utility tie against every other scorer, including `combat_retreat` and `recover` (survival-urgency scorers). This directly contradicts the design doc's own framing of adventure as "routine, non-urgent activity" belonging at "the generic, lowest-priority fallback" (§2). **Recommendation for Plan**: choose a value that sorts *after* `"town_return"` (the current alphabetical maximum) so `ADVENTURE_ROUTE` never wins a tie against any of the other 10 existing kinds — e.g. a value in the `"w"`-`"z"` range, disclosed with an inline comment explaining the deliberate ordering rationale (ties are rare in practice given float utility, but AC6 explicitly requires "not an arbitrary" choice, so the reasoning must be recorded, not just the value).
6. **`AdventureRouteScorer`'s `~2.9` ceiling is "estimated" per the mechanics doc's own §6.6 heading** ("Score Range Summary (Estimated, No Blockers)") — the design doc's own §3 flags this needs "empirical validation once real ... not assumed correct by formula alone." This ticket's normalization constant (`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, already defined at `intelligence.py:32`, reused not redefined) is inherited, not newly chosen — no action needed here beyond citing the existing constant, but Implement should not treat "2.9 normalizes to exactly 100.0" as load-bearing beyond the literal formula (AC2's "raw_score of 2.9 normalizes to utility==100.0 exactly" is a formula-identity claim, trivially true by construction, not an empirical claim about real route scores reaching 2.9).

## Anti-Drift Hazards

- **Do not modify `src/domains/adventure/phase.py` in this ticket.** It is not in the ticket's `## Scope` list (only `## Related Code Areas`, for situational awareness). `AdventureDecisionPhase` stays fully active and wired (`pipeline.py:237-244`, confirmed unmodified). `AdventureGoalScorer` must **import** `_resolve_cognition_profile_id`/`_supports_adventure_routing` from `src.domains.adventure.phase` (reuse-by-import), not move/duplicate them — physically relocating them (as design doc §5's "Relocated" section describes for the *end state* of the whole epic) would either break `phase.py`'s own use of them (if moved without a shim) or require touching `phase.py` to re-import them back (itself an undisclosed scope-creep edit to a file this ticket doesn't own). Physical relocation is implicitly C3's job (the ticket that deletes `AdventureDecisionPhase` and can safely retire `phase.py`'s copies).
- **Do not touch `src/engine/pipeline.py`.** Confirmed unmodified by this ticket (C3's job, gated on this ticket + C4).
- **Do not implement `_threat_resolved()` relocation or `evaluate_project_switch()`'s `state` parameter addition.** Confirmed out of scope (C2's job) — `evaluate_project_switch()`'s current signature (`entity, candidate_project, current_tick`, no `state`) is unchanged by this ticket; the new materialization branch must fit within that existing signature (it does — `RouteToProjectMapper.map_to_states()` doesn't need `state` either).
- **Do not build a shadow-mode comparison test or wire a SimQ pre-cutover gate.** Confirmed C4's job.
- **Do not use `best_candidate.utility` anywhere in the materialization branch's `score=` argument.** This is the single highest-value regression to guard against — see AC3/AC4 and design doc §4's worked arithmetic. The dedicated regression test (test_plan.md) must assert the materialized `ProjectState.score` equals the *raw* score, with a concrete numeric example demonstrating the scale mismatch would otherwise occur (mirroring `test_score_normalization.py`'s existing style of showing the broken-vs-fixed arithmetic inline in the test docstring).
- **Do not silently resolve the target/target_pos gap (Risk #1) by weakening the tier-5 floor check itself** (`intelligence.py:1373`) — that check is shared by all 11 scorers, not adventure-specific; any fix belongs in `AdventureGoalScorer.score()`'s own construction of `target_id`, not in the shared gate.
- **Do not change `RouteFamily`, `_MAP`, or any of the 15 mapped `(ProjectKind, ObjectiveKind)` pairs.** This ticket wraps `RouteToProjectMapper` unchanged; any felt need to add/adjust a mapping belongs to a different ticket.
- **Do not attempt to close `STRAT-185`'s null `test_path` as a requirement** — it's explicitly a nice-to-have per the ticket's own Assumptions section; only close it if a natural test lands that genuinely exercises its `text` claim, don't force one into existence.
