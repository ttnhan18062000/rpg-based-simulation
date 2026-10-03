---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE
artifact_type: investigation
tags: [testing, cognition, adventure, feature-flags]
---

# Investigation — TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE

## Current Behavior

### The two decision paths (both confirmed pure — neither mutates `state`)

**`AdventureDecisionPhase.apply()`** — `src/domains/adventure/phase.py:82-198`
```python
@staticmethod
def apply(
    state: AuthoritativeState,
    context: Optional[dict] = None,
    trace_writer: Optional[Any] = None,
    faction_directives: Optional[list] = None,
    factions: Optional[Any] = None,
) -> StateUpdate:
```
Loops all eligible heroes (`_supports_adventure_routing` + alive + active + not
lock-blocked/`_threat_resolved`), and per hero: builds `opportunities` from
`ResourceOpportunityProvider`/`ServiceOpportunityProvider` (phase.py:133-136), calls
`AdventureRouteGenerator.generate(hero, state, opportunities=opportunities)` (phase.py:137), calls
`AdventureDecisionService.decide(hero, candidates, tick=tick, resource_nodes=state.resource_nodes,
faction_directives=faction_directives, factions=factions)` (phase.py:140-145), then if a project was
proposed, calls `StrategicIntelligenceSystem.evaluate_project_switch(hero, result.proposed_project,
tick, state=state)` (phase.py:170-172) and packs the result into `entity_updates[hero.id]`. Returns a
`StateUpdate` (phase.py:198). Every line that touches `state` is a read (`state.entities.values()`,
`state.resource_nodes`, passed into helper calls) — no attribute assignment, no dict/list mutation of
anything reachable from `state`. `AuthoritativeState` and its component dataclasses are
`@dataclass(frozen=True, slots=True)` (`src/core/state.py:1080` and throughout), so any attempted
top-level attribute reassignment would raise `FrozenInstanceError` at the point of the attempt — this
class of mutation is impossible by construction, not just by convention.

**`AdventureGoalScorer.score()`** — `src/ai/goals/adventure_scorer.py:30-168`
```python
def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
```
Replicates the *exact same* three-call sequence for one entity: eligibility check
(`_supports_adventure_routing`, imported lazily from `phase.py`), then
`opportunities = ResourceOpportunityProvider.get_opportunities(entity, state) +
ServiceOpportunityProvider.get_opportunities(entity, state)` (lines 84-87),
`AdventureRouteGenerator.generate(entity, state, opportunities=opportunities)` (line 88),
`AdventureDecisionService.decide(entity, candidates, tick=state.tick,
resource_nodes=state.resource_nodes, faction_directives=None, factions=state.factions)` (lines 89-96).
Returns a `GoalScore` (frozen dataclass, `src/ai/goals/base.py:8-13`) carrying
`metadata={"route_family": family, "raw_score": raw_score}`. Same read-only relationship to `state` —
confirmed no assignment/mutation anywhere in the method or in `_resolve_placeholder_target_pos()`
(lines 170-230), which only reads `state.entities`/`entity.navigation.position`/`state.town_center`
and calls `SpatialQueryService.nearest_building` (read-only query service).

Materialization for a winning `ADVENTURE_ROUTE` candidate happens in
`StrategicIntelligenceSystem.evaluate_strategic_intent()` (`src/systems/strategic_systems/
intelligence.py:1440-1467`, landed by TCK-20260811-ADVENTURE-GOAL-SCORER): when
`best_candidate.kind == GoalKind.ADVENTURE_ROUTE`, it calls
`RouteToProjectMapper.map_to_states(family=best_candidate.metadata.get("route_family"),
entity_id=entity.id, target=best_candidate.target_id, target_pos=best_candidate.target_pos,
tick=current_tick, score=best_candidate.metadata.get("raw_score", 0.0))` — confirmed using
`raw_score`, never `utility` (this was the exact defect class §4 of the design doc calls out and
ticket 1 fixed correctly). `evaluate_strategic_intent(state, entity, force=False, cadence=None)` is
itself a single-entity function (`intelligence.py:1173-1178`) — it can be called in isolation for one
constructed entity/state without running the tick pipeline, **but** it runs *all* registered
`GoalScorer`s via `GoalRegistry.get_all_scores(entity, state)` (`base.py:46-50`) and only materializes
`ADVENTURE_ROUTE` if it wins tier-5 arbitration against every other candidate (Town/Recover/Sleep/
Combat/etc.). For a shadow test this is a real fragility: guaranteeing `ADVENTURE_ROUTE` wins against
10 other real scorers depends on constructing a scenario where nothing else clears the tier-5 floor
first. **Recommended, more deterministic approach for the shadow test:** call
`AdventureGoalScorer().score(entity, state)` directly (no `GoalRegistry` involvement — it is a plain
instance method needing only `entity`/`state`), then, if the AC wants the materialized
`ProjectState`/`ObjectiveState` shape compared too, invoke
`RouteToProjectMapper.map_to_states(family=result.metadata["route_family"], entity_id=entity.id,
target=result.target_id, target_pos=result.target_pos, tick=state.tick,
score=result.metadata["raw_score"])` directly in the test — this is *exactly* what
`intelligence.py:1450-1457` does, replicated deterministically without depending on tier-5 arbitration
outcome. This satisfies AC1's "materialization independently" language without introducing
arbitration-outcome flakiness.

### `RouteToProjectMapper._MAP` — confirmed 15 entries (`src/domains/adventure/mapper.py:31-47`)
`RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, TRAIN_SKILL, TAKE_EASY_QUEST, HUNT_WEAK_ENEMY,
GATHER_RESOURCE, SELL_LOOT_FOR_GOLD, ASK_INFORMATION, SCOUT_LOCATION, FORM_PARTY, RETURN_TOWN,
QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL`. `RouteFamily` has 16 members total
(`test_route_family_definitions_are_unique` asserts `len(values) == 16`); only `DEFER_WITH_REASON`
is excluded from `_MAP`, matching the ticket's "15 route families" claim exactly.

### CRITICAL FINDING — 9 of the 15 mapped families are unreachable through the real generation
pipeline today

`AdventureRouteGenerator.generate()` (`src/domains/adventure/generator.py:24-181`) is the **only**
function anywhere in `src/` that constructs an `AdventureRouteOption` with a family assigned from
scratch. Its `kind_map` (generator.py:38-45) is a closed, hardcoded 6-entry dict:
```python
kind_map = {
    "gather_resource": RouteFamily.GATHER_RESOURCE,
    "buy_item": RouteFamily.BUY_UPGRADE,
    "craft_item": RouteFamily.CRAFT_UPGRADE,
    "repair_gear": RouteFamily.RECOVER,
    "ask_information": RouteFamily.ASK_INFORMATION,
    "rest_inn": RouteFamily.RECOVER,
}
```
`Opportunity.kind`'s own type comment (`src/world/providers/resources.py:11`) confirms this is the
complete, documented closed set: `kind: str  # "gather_resource" | "buy_item" | "craft_item" |
"repair_gear" | "ask_information" | "rest_inn"`. Beyond opportunity-backed routes, `generate()` adds
exactly three forced/structural routes (RECOVER on low-health/healing need, ASK_INFORMATION on
weak-weapon/equipment need with no buy/craft option present, FORM_PARTY when sociability ≥ 0.2 and
allied candidates exist) and one DEFER_WITH_REASON fallback. That is **7 families total**
(`GATHER_RESOURCE, BUY_UPGRADE, CRAFT_UPGRADE, RECOVER, ASK_INFORMATION, FORM_PARTY,
DEFER_WITH_REASON`) that `generate()` can ever produce from a real `AuthoritativeState`.

`AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) has real, family-specific scoring
branches for the other 9 (`TRAIN_SKILL, TAKE_EASY_QUEST, HUNT_WEAK_ENEMY, SELL_LOOT_FOR_GOLD,
SCOUT_LOCATION, RETURN_TOWN, QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL` — e.g. lines 126, 138,
148, 159, 199-209, 243, 251, 264-266) — it can *score* a candidate with one of these families if
handed one, but it never *constructs* one; it only reads `route.family` on options that were already
built elsewhere. Grepped project-wide (`grep -rn "RouteFamily\.\(TRAIN_SKILL\|TAKE_EASY_QUEST\|
HUNT_WEAK_ENEMY\|SELL_LOOT_FOR_GOLD\|SCOUT_LOCATION\|RETURN_TOWN\|QUEST_OPPORTUNITY\|PROTECT_TARGET\|
OWN_SURVIVAL\)" src/`): the only *constructions* of these 9 are `_MAP`'s dict keys (mapper.py) and
`scoring.py`'s dict-literal weight tables — never an `AdventureRouteOption(family=RouteFamily.X, ...)`
call. `PROTECT_TARGET`/`OWN_SURVIVAL` (E41D escort routes) are the closest to "real": `scoring.py:257-
266` has live escort-reprioritization logic keyed on `group.escort_target_id`, but it only
*re-weights* a route whose family is *already* `PROTECT_TARGET`/`OWN_SURVIVAL` — nothing in
`generator.py` or elsewhere ever assigns those two families to a freshly generated candidate either.

**Consequence for AC2 as literally worded:** "For each of the 15 route families, the test asserts
both paths select the same winning route family... for representative scenario fixtures" cannot be
satisfied end-to-end (i.e. via a constructed `AuthoritativeState` driving the real
opportunities→generate()→decide() pipeline through both `AdventureDecisionPhase.apply()` and
`AdventureGoalScorer.score()`) for 9 of the 15 families, because neither path's real call chain can
ever select them as winner today — `generate()` structurally cannot produce them. This is not a gap
in this ticket's test-writing effort; it is a pre-existing gap in the adventure-routing feature
itself (9 of `RouteFamily`'s mapped members are dead code from the generator's perspective), invisible
until this ticket tried to build per-family fixtures for all 15.

## Resolution of the scenario-corpus open question (ticket Assumption #1)

**Two-tier resolution, not a single blanket answer:**

1. **The 6 real-generation-reachable families** (`RECOVER, BUY_UPGRADE, CRAFT_UPGRADE,
   GATHER_RESOURCE, ASK_INFORMATION, FORM_PARTY`): build genuine `AuthoritativeState` scenarios (one
   `EntityState` + supporting `resource_nodes`/`buildings`/self-model weaknesses per family) and run
   **both** `AdventureDecisionPhase.apply(state)` and `AdventureGoalScorer().score(entity, state)`
   against the same state, asserting matching `family`/`raw_score`. **Reuse
   `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`'s `_state(entities)`
   helper** (lines 18-47) as the fixture-construction pattern — it builds a complete, valid
   `AuthoritativeState` with every required field and is already exercised against
   `AdventureDecisionPhase.apply(state)` directly (see `test_filters_out_locked_projects`,
   `_build_hero_with_active_system_b_lock`). **This corrects the ticket's own stated Assumption**,
   which named `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py` as "the most
   likely reuse candidate": that file does **not** build a full `AuthoritativeState` at all — its
   `_entity()` helper builds only an `EntityState`, and its tests hand-construct
   `AdventureRouteOption` objects and call `AdventureDecisionService.decide()` directly (bypassing
   `ResourceOpportunityProvider`/`ServiceOpportunityProvider`/`AdventureRouteGenerator.generate()`
   entirely). It is well-suited to testing `decide()`'s scoring/tie-break logic in isolation, but
   structurally cannot exercise the thing this ticket needs to shadow-test: the *wrapping* difference
   between `AdventureDecisionPhase.apply()` and `AdventureGoalScorer.score()`, which lies entirely in
   how each path drives opportunities→`generate()`→`decide()`, not in `decide()` itself.
2. **The 9 currently-unreachable families**: cannot be end-to-end shadow-tested through either real
   call path today (see Critical Finding above) — building a "representative AuthoritativeState
   scenario" for e.g. `HUNT_WEAK_ENEMY` or `SCOUT_LOCATION` is not possible without first extending
   `generator.py`'s `kind_map`/opportunity providers, which is out of this ticket's scope (out of
   scope per the ticket's own "Building AdventureGoalScorer itself" boundary — extending the
   generator is arguably further still). The realistic, honest coverage for these 9 is
   mapper/schema-level parity only: both paths call the *identical*
   `RouteToProjectMapper.map_to_states()`/`get_kinds()` for any family handed to them, so parity for
   these 9 is a property of the mapper being a pure, single, shared function — already partially
   proven by `tests/unit/domains/adventure/test_phase3_route_families.py`
   (`test_route_family_has_project_mapping` iterates all `RouteFamily` members including all 15
   mapped ones). **Flagging this as a disclosed, not-hidden scope boundary is required** — the Plan
   phase must decide explicitly whether AC2's "for each of the 15 route families" is satisfied by
   (a) 6 real end-to-end shadow comparisons + 9 mapper-level-only comparisons, both documented as
   such in the diff report, or (b) a scope amendment. This investigation recommends (a): it is the
   only technically honest reading of "representative scenario fixtures" given current code, and
   silently only testing a subset without saying so would violate CLAUDE.md's "no known material gap
   left unstated" rule.

## How "neither committed a change to state" would actually be verified

`AuthoritativeState` is `@dataclass(frozen=True, slots=True)` (`src/core/state.py:1080`) and contains
several `Dict`/`set`/`list` fields (`entities`, `resource_nodes`, `factions`, etc.) — **this makes the
instance itself unhashable** (Python's generated `__hash__` for a frozen dataclass hashes a tuple of
field values, and hashing a `dict` field raises `TypeError` the moment `hash()` is actually called).
So the ticket's own parenthetical "(pre/post equality or hash check)" needs to resolve to **equality
via the repo's existing `CanonicalStateHasher`, not Python's built-in `hash()`**:
`src/engine/checkpoint.py`'s `CanonicalStateHasher.get_hash(state) -> str` produces a SHA-256 of a
canonical (sort-keys, dict-order-insensitive) JSON serialization of the whole state — this is real,
existing, already-used-for-exactly-this-purpose infrastructure, not something to build new.
**Precedent already in the test suite**: `tests/integration/pipeline/test_no_hidden_mutation.py` uses
this exact pattern (`hash_1 = CanonicalStateHasher.get_hash(next_state_1)` etc.), and
`tests/integration/kernel/test_snapshot_integrity.py::test_hash_stability_with_dict_order` +
`test_auth_state_is_frozen`/`test_entity_state_is_frozen` are the direct precedent for "prove no
mutation" tests in this codebase. Concretely for this ticket's shadow test:
```python
hash_before = CanonicalStateHasher.get_hash(state)
AdventureDecisionPhase.apply(state)          # discard the StateUpdate; only checking state itself
AdventureGoalScorer().score(entity, state)
hash_after = CanonicalStateHasher.get_hash(state)
assert hash_before == hash_after
```
`CanonicalStateHasher.get_hash()` is called directly (not through `CanonicalHashScheduler`), so the
`HashScheduleViolation` gate (`checkpoint.py:29-33`, enforced only inside
`CanonicalHashScheduler.allow_full_hash_at`, `checkpoint.py:218-244`) does not apply — direct
`get_hash()` calls in tests are the established, ungated pattern (confirmed by the 3 precedent test
files above, none of which go through the scheduler). No new hashing utility is needed.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §2 (Goal Hierarchy) and §6.6/§6.8 (score normalization,
  `_ADVENTURE_ROUTE_SCORE_MAX`) — both already updated by TCK-20260811-ADVENTURE-GOAL-SCORER to
  describe `AdventureGoalScorer` as "not yet live." This ticket does not change wiring or live
  behavior (`pipeline.py` is untouched, per ticket Scope), so these sections remain accurate as-is —
  only a forward-reference note ("shadow-parity proven, see STRAT-xxx") is warranted, not a rewrite.
- Design doc `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
  §7 (Migration/rollout plan, step 2) and §9 (Testing) are the direct source of this ticket's scope —
  §9 explicitly calls the 15-family materialization-shape-fidelity test out as required, and separately
  flags `STRAT-185`/`STRAT-186`/`STRAT-187` (P0, `test_path: null` for STRAT-185 specifically) as "a
  real opportunity to close" via this work. `STRAT-186`/`STRAT-187` already have `test_path` filled
  (closed by TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG) — only `STRAT-185` (text:
  "Strategic project retention is bounded by interruption resistance") remains `test_path: null`.
  This ticket's shadow test is about *cross-path parity*, not interruption-resistance retention
  specifically — it is a plausible but not obviously-correct fit for STRAT-185's `test_path`. Flagged
  as an open question for Plan, not assumed.

## Docs Requiring Update

- `docs/parity_ledger/strategic_cognition.yaml`: add a new entry documenting the shadow-mode
  raw_score/route-family parity proof between `AdventureDecisionPhase` and `AdventureGoalScorer`
  (status: verified, priority: P1 since `DELETE-ADVENTURE-DECISION-PHASE`'s own AC1 hard-gates on
  this ticket being DONE — a P1, not P0, since nothing live depends on it yet), citing the new test
  file(s) as `test_path`, and explicitly noting which 6 of the 15 route families were end-to-end
  verified vs. which 9 were mapper-level-only (per the Critical Finding above) so the entry does not
  overstate coverage.
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-252's existing entry (`strategic_cognition.
  yaml:3255-3288`) says the scorer is "not yet the live/wired decision path" and cites
  `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE landing first` as a prerequisite for the next step —
  once this ticket lands, that citation should get a one-line addendum ("this prerequisite is now
  satisfied") so a future reader doesn't have to cross-reference ticket status manually.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: §7's
  migration-plan step 2 should be marked complete (a short "Status: done, see
  TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE" note), consistent with how design docs in this repo
  track staged-rollout completion.

## Parity Ledger Overlap

- `STRAT-185` (P0, `strategic_cognition.yaml:1987-1996`) — "Strategic project retention is bounded by
  interruption resistance," `test_path: null`. Design doc §9 flags this as a closeable gap via this
  work; this investigation is not confident the shadow test's own assertions (route-family/raw_score
  parity) are the right `test_path` for THIS specific claim (retention bound, not cross-path parity).
  **Open question for Plan — do not assume an answer.**
- `STRAT-186`/`STRAT-187` (P0, already `test_path`-filled by a prior ticket) — not directly touched by
  this ticket; no action needed.
- `STRAT-236` (P1, `:2708-2718`) — describes the threat-resolved early-release gate; unaffected by
  this ticket's scope (shadow test only observes existing behavior, doesn't change it).
- `STRAT-252` (P2, `:3255-3288`) — the ADVENTURE-GOAL-SCORER entry; needs the one-line addendum noted
  above once this ticket's test exists and passes.
- No P0 entry is newly created or newly required to pass by this ticket beyond the STRAT-185 open
  question.

## Prior Work

- `tickets/done/TCK-20260811-ADVENTURE-GOAL-SCORER.md` — built `AdventureGoalScorer` exactly as
  described in Current Behavior above; its own Files Changed/Completion Summary confirm the scorer is
  "registered but intentionally not yet wired into `src/engine/pipeline.py`," matching this ticket's
  own framing.
- `tickets/done/TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION.md` — relocated `_threat_resolved()`
  into `intelligence.py` and generalized the lock-expiry condition; touched the same file
  (`intelligence.py`) as ticket 1's materialization branch, but at a different location — confirmed no
  line-number drift affecting the `ADVENTURE_ROUTE` branch (verified fresh at `intelligence.py:1440-
  1467` this session, matching STRAT-186/187's own re-verified citations after that ticket).
  `phase.py:21` imports `_threat_resolved` from `intelligence.py` directly — unaffected by this
  ticket's scope.
- `tickets/todos/adventure-cognition-merge/TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md` — the
  gated follow-up ticket. **Its AC1 already reads**: "This ticket's Implement phase does not proceed
  until TCK-20260811-ADVENTURE-GOAL-SCORER (C1) and TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4)
  are both in tickets/done/... if not, this ticket is held/blocked." **This ticket's own AC4
  ("AdventureDecisionPhase removal is gated... encoded as a hard dependency") is therefore already
  satisfied by pre-existing ticket text** — no edit to `DELETE-ADVENTURE-DECISION-PHASE.md` is
  required by this ticket's Implement phase; AC4 just needs verification/citation, not new authoring.
- `tests/integration/pipeline/test_no_hidden_mutation.py` and
  `tests/integration/kernel/test_snapshot_integrity.py` — established precedent for no-mutation
  proofs via `CanonicalStateHasher`/frozen-dataclass assertions (see above).

## Risks and Open Questions

1. **(Blocking for Plan) STRAT-185's `test_path`**: is the shadow test the right fit, or should
   STRAT-185 stay open pending a dedicated interruption-resistance-retention test? Do not assume;
   Plan must decide and state the reasoning either way.
2. **(Blocking for Plan) AC2's "15 route families" scope resolution**: confirm the two-tier
   resolution above (6 end-to-end + 9 mapper-level) is acceptable, or that AC2 needs to be
   re-scoped/amended given the 9-family generator gap is a genuine, pre-existing limitation this
   ticket did not create.
3. **`factions` parameter divergence (non-blocking, but must be handled explicitly in the test, not
   relied on coincidentally)**: `AdventureDecisionPhase.apply(state)` defaults its `factions` kwarg
   to `None` if the test doesn't pass it explicitly, while `AdventureGoalScorer.score()` always passes
   `state.factions` (default `{}` per `AuthoritativeState`'s `field(default_factory=dict)`,
   `src/core/state.py:1156`) into `decide()`. For a scenario with no real faction state, `factions={}`
   and `factions=None` currently produce identical output in `AdventureRouteScorer.score()`'s escort
   branch (`scoring.py:133`: `factions is not None and any(...)` — an empty dict makes `any()` False
   the same way `factions is not None` being False does) — but this is a *coincidence* of the current
   escort-branch implementation, not a structural guarantee. The shadow test should call
   `AdventureDecisionPhase.apply(state, factions=state.factions)` explicitly to match call-signature
   parity rather than depend on this coincidence remaining true.
4. **Pre-existing "wins but stalls" bug, live in the CURRENT path (not introduced by this epic, not
   caught by AC2 as scoped)**: ticket 1's own Implementation Notes document, in detail, that
   `RECOVER`/`ASK_INFORMATION`/`FORM_PARTY` (the 3 forced/structural route families that never carry
   `target_node_id`/`source_opportunity_ids`) previously produced `target_pos=None` in
   `AdventureGoalScorer`'s new path and would "win but stall forever" — fixed there via
   `_resolve_placeholder_target_pos()`. Reading `AdventureDecisionService.decide()`
   (`src/domains/adventure/service.py:132-148`) directly: it sets `target_pos = None` **unconditionally**
   (line 135, never assigned otherwise) before calling `RouteToProjectMapper.map_to_states(...,
   target_pos=target_pos, ...)` — meaning the **currently-live** `AdventureDecisionPhase` path has
   never set `target_pos` for *any* route, including these 3 forced families, and should exhibit the
   same stall risk today in production. This is a real, pre-existing, currently-live gap this
   investigation surfaced as a side effect, **not** something AC2 (family + raw_score comparison only)
   would ever catch, since family and raw_score are identical between the two paths for these 3
   families — only `target_pos`/tactical resolvability differs, and AC2 doesn't compare that
   dimension. Recommend flagging this honestly in the diff report's scope note ("this test does not
   compare target_pos/tactical-resolvability between paths") and filing a separate follow-up ticket
   for the live-path stall risk — out of this ticket's scope to fix, but should not be silently
   omitted per CLAUDE.md's "no known material gap left unstated" rule.

## Anti-Drift Hazards

- **Do not let the shadow test silently only cover the 6 reachable families while claiming "all 15"**
  in its docstring/name — the diff report and any parity ledger entry must explicitly state the 6-vs-9
  split (see Critical Finding).
- **Do not fix the `target_pos` live-path gap (#4 above) inside this ticket** — it's a real,
  independently-discovered bug in the *current live* path, out of this ticket's Scope (which is
  test-writing + `/simq-audit` invocation only, per the ticket's Out of Scope section explicitly
  excluding "Building AdventureGoalScorer itself"). Fixing it here would be undisclosed scope creep
  into `AdventureDecisionPhase`/`AdventureDecisionService`, both of which the ticket's own Related
  Code Areas do not list as owned by this ticket for modification (only for reading, as the shadow
  comparison target).
- **Do not use `hash()`/`__hash__` directly on `AuthoritativeState`** — it will raise `TypeError` given
  the dict-typed fields; always route through `CanonicalStateHasher.get_hash()`.
- **Do not reuse `test_phase3_adventure_decision_scenarios.py`'s pattern** (hand-built
  `AdventureRouteOption` + direct `AdventureDecisionService.decide()` call) for the shadow test itself
  — it bypasses the exact wrapping logic (`generate()`/opportunity-provider calls) that is the real
  parity risk between the two paths; it is fine to keep using for `decide()`-level unit tests, just
  not as the shadow-test's own state-construction source.
- **Do not let the `/simq-audit` "step 4" AC turn into building new SimQ tooling** — the ticket's Out
  of Scope section is explicit ("Reimplementing /simq-audit's Recalibrate/Classify-Drift/Report
  machinery"); this ticket's job is only to *invoke* the existing workflow and record its returned
  verdict (`DONE_NO_TICKET` / `NEEDS_TICKET` / `ANCHORS_STILL_FAILING` / `BLOCKED`, plus the
  underlying Classify Drift `verdict`: `no_regression` / `regression` / `needs_da_decision`) in the
  ticket's own Implementation Notes/Completion Summary — not a pytest assertion.
