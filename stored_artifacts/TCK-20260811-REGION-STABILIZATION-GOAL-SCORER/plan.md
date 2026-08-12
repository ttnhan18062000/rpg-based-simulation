---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
artifact_type: plan
tags: [cognition, world]
---

# Implementation Plan — TCK-20260811-REGION-STABILIZATION-GOAL-SCORER

## Summary

Add `ProjectKind.STABILIZE` and a new `GoalKind.REGION_STABILIZATION` enum member to
`src/core/strategic.py`. Extract the pure hazard-threshold/urgency math currently inline in
`EventInterpreter.interpret_regional_danger()` (`src/systems/world_systems/events.py`) into a new
static helper, `EventInterpreter.compute_danger_urgency(region)`, and simplify
`interpret_regional_danger()` down to concern-generation only (no more stabilize-project
construction, no more direct `current_project_id_set` write). Add a new
`RegionStabilizationGoalScorer` in a new co-located module,
`src/ai/goals/region_stabilization_scorer.py`, mirroring `AdventureGoalScorer`'s/
`SocialContractGoalScorer`'s file placement and wrapper shape exactly: it resolves the entity's
current region via `LegalityServiceV2.get_region_for_position()` (the codebase's own established
convention for "entity's current region," confirmed used by `src/world/ecology.py`,
`regional_sovereignty.py`, `boss.py`, `spawn.py`, `calamity.py`, `influence.py`, `camp.py`), calls
the new shared helper, and — critically — **recalibrates** the raw score from the original method's
`urgency * 100` to `urgency * _ADVENTURE_ROUTE_SCORE_MAX` (2.9), because `ProjectKind.STABILIZE`
being a real `ProjectKind` now routes the materialized project onto `_score_scale_max()`'s 2.9-ceiling
scale, not the 100-ceiling scale the original bare-string `kind="stabilize"` fell through to by
default. Register the scorer in `src/ai/goals/__init__.py`. Add a new
`elif best_candidate.kind == GoalKind.REGION_STABILIZATION:` materialization branch in
`StrategicIntelligenceSystem.evaluate_strategic_intent()` (`src/systems/strategic_systems/
intelligence.py`) that is a "dumb" consumer of `proj_kind`/`obj_kind` resolved upstream in the scorer
and carried through `GoalScore.metadata` — needing zero new imports in `intelligence.py`, exactly
mirroring ticket 5's `SOCIAL_CONTRACT` branch shape. Never `best_candidate.utility` in
`ProjectState.score` — always `metadata["raw_score"]`.

**Reachability disclosure (the single most consequential decision in this plan):** unlike ticket 5's
`SocialContractGoalScorer` (whose live-reachability rode on an independent, already-live production
writer, `execute_recruit()`), `interpret_regional_danger()` has no independent live writer this scorer
could instead read from — the entire hazard-threshold/urgency decision lives inside a method nothing
calls. This plan chooses **option (a)** from investigation.md's Risk #1: the new scorer duplicates
(via the extracted, shared helper) the hazard-threshold/urgency decision and reads `state.regions`
directly through `LegalityServiceV2.get_region_for_position()`. `evaluate_strategic_intent()` is
reached from `pipeline.py:333`'s `run_phase("strategic_intelligence", ...)` — a real, live pipeline
phase that runs every tick with no feature-flag guard (confirmed by direct read) — but the per-entity
`.score(entity, state)` call inside it is **not** unconditional every tick for every entity: entities
are first narrowed to a tiered, budgeted `candidate_ids` subset by `StrategicWorkQueue.build()`
(`src/systems/strategic_systems/work_queue.py`, default `budget=50`), and each candidate is then gated
by `should_run(state.tick, e_id, cadence.strategic_intelligence)` (`src/engine/cadence.py`,
`SystemCadence.strategic_intelligence` defaults to every 10 ticks, per-entity-staggered). This is the
same cadence/budget throttling every other tier-5 scorer (`ADVENTURE_ROUTE`, `SOCIAL_CONTRACT`)
already operates under — not a special restriction added for this ticket. Within that existing
cadence, **registering `RegionStabilizationGoalScorer` makes LEG-RPG-116 (regional-danger-driven
stabilization) live-reachable in production for the first time ever** — cadence-gated and
work-queue-budgeted, the same way its sibling scorers are reachable, not "unconditional every tick" —
which is still a genuine, disclosed behavior-availability change, not merely "closes an arbiter bypass
on an already-live path" the way ticket 5's framing did. This must be stated exactly this way (live,
cadence/budget-gated, first-time-reachable) in every doc/ticket location that describes this ticket's
impact — never as "no production impact" (that would be true only for `interpret_regional_danger()`
specifically, not for the mechanic as a whole), never overstated as "unconditional every tick," and
never silently implied to have already been live before this ticket (it was not — confirmed no
production caller anywhere, investigation.md, re-confirmed here).

## Design Decisions (resolves the 6 open questions flagged for this plan)

**#1 — Reachability (investigation.md Risk #1).** Chosen: **option (a)** — the scorer re-implements
the region-danger decision by calling a newly extracted, shared static helper,
`EventInterpreter.compute_danger_urgency(region: RegionState) -> Optional[float]`
(`src/systems/world_systems/events.py`, new method, Step 3), and resolves "the entity's current
region" via `LegalityServiceV2.get_region_for_position(entity.navigation.position, state)`
(`src/engine/legality.py:44-46`, confirmed read directly: `return SpatialQueryService.get_region_at(state, pos)`
— the exact helper 7+ other call sites in `src/world/` already use for this exact "entity's current
region" lookup, not a bespoke resolution this plan invents). **Not option (b)**: wrapping
`interpret_regional_danger()` unchanged is structurally infeasible without changing its signature
(`(entity, region, current_tick) -> Optional[StrategicUpdate]`, incompatible with
`GoalScorer.score(entity, state) -> GoalScore`) — and this plan must edit that method anyway to
satisfy AC2 (remove the direct `current_project_id_set` write), so preserving it "unchanged" was never
actually available as a clean option once AC2 is satisfied. **Not option (c)** (land wrapper
unit-test-correct only, stay fully inert): rejected because the ticket's own AC3 requires the scorer
to "produce a comparable `GoalScore` that must clear `evaluate_project_switch()` to become
`current_project_id`" — a `GoalScore` with no live data source behind it (i.e., one that can only ever
be exercised by tests constructing a `state.regions` fixture by hand) would satisfy AC3's letter but
not its evident intent, and `GoalRegistry.get_all_scores()`'s calling convention (`base.py:46-50`)
gives every registered scorer a real `AuthoritativeState` to read from regardless — there is no way to
register the scorer at all without it becoming reachable via the same cadence/budget-gated path every
other tier-5 scorer already uses (not literally "every tick," see Design Decision #1's correction).
**Disclosure obligation**: this
is recorded verbatim, not softened, in Docs Requiring Update (Step 10) and must appear in the ticket's
own Implementation Notes at Finalize.

**#2 — Enum-member gap scope (investigation.md's "Net finding for Plan").** Confirmed independently
by direct read (`src/core/strategic.py:121-156`): only `ProjectKind.STABILIZE` is missing. `"investigate"`
(`ObjectiveState.kind` in `interpret_regional_danger()`) already equals `ObjectiveKind.INVESTIGATE`
(`strategic.py:104-116`) and `"exploration"` (`interpret_scar_detection()`, out of scope) already
equals `ProjectKind.EXPLORATION`. Chosen: add `ProjectKind.STABILIZE = "stabilize"` (Step 1) — the
clean choice per investigation.md's own reasoning (matches the raw string already in use, mirrors
`DirectiveKind.STABILIZE`'s existing naming convention, "recovery"/"combat" are semantically worse
fits). No `ObjectiveKind` addition needed; `ObjectiveState.kind` for the stabilize objective is
upgraded to the literal `ObjectiveKind.INVESTIGATE` enum member (not just the coincidentally-matching
string) as part of Step 6's materialization branch, mirroring ticket 5's Step 8 enum-upgrade
discipline.

**#3 — New `GoalKind` member name and tie-break value (investigation.md Risk #3).** Chosen:
`GoalKind.REGION_STABILIZATION = "region_stabilization"` (Step 2). Verified against the current
12-member `GoalKind` enum (`strategic.py:121-141`, read directly: 10 originals +
`ADVENTURE_ROUTE = "z_adventure_route"` + `SOCIAL_CONTRACT = "social_contract"`) — no collision with
any existing `GoalKind` value, and no collision with any `ProjectKind` value including the new
`ProjectKind.STABILIZE = "stabilize"` (`"region_stabilization" != "stabilize"`, confirmed by direct
string comparison, not assumed — this is the specific, deliberate choice that resolves Design
Decision #4 below). Tie-break: `modified_scores.sort(key=lambda x: (-x.utility, x.kind))`
(`intelligence.py:1408`, confirmed unchanged) sorts ties by ascending string value, and the loop below
picks the **first** (i.e., alphabetically **smallest**) tied candidate as `best_candidate`
(`intelligence.py:1412-1418`). `"region_stabilization"` sorts: **after** `"recover"` (`r-e-c` <
`r-e-g`, so `RECOVER` still wins an exact tie against regional stabilization — personal
recovery/healing plausibly should outrank a regional crisis when literally tied), and **before**
`"resolve_blocker"`, `"social"`, `"social_contract"`, `"town_return"`, and `"z_adventure_route"`
(`r-e-g` < `r-e-s`/`s`/`s`/`t`/`z` respectively) — so `REGION_STABILIZATION` wins ties against
`SOCIAL_CONTRACT` and `ADVENTURE_ROUTE`, matching investigation.md's own qualitative reasoning
("does region-crisis urgency deserve to out-rank an accepted social obligation and routine
adventuring? Qualitatively yes"). Disclosure: this specific interleaving (loses only to `RECOVER`
among the other 11 members) is an **incidental consequence** of choosing a readable, descriptive
string value, not an exhaustively-reasoned pairwise ranking against each of the other 11 — the same
level of rigor tickets 1 and 5 applied to their own tie-break choices (neither reasoned about every
pairwise position against the original 10 either, only the mutual position of the tier-5 additions
relative to each other).

**#4 — Resume/dedup lookup collision (investigation.md Risk #4).** Chosen: **no collision** —
`GoalKind.REGION_STABILIZATION`'s value (`"region_stabilization"`) is deliberately distinct from
`ProjectKind.STABILIZE`'s value (`"stabilize"`), so `existing = next((p for p in strat.projects.values()
if p.kind == best_candidate.kind), None)` (`intelligence.py:1429`, confirmed unchanged) never matches
a `REGION_STABILIZATION` winner — same accepted, inert dedup gap `ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`
already share. Rationale for **not** deliberately engineering the collision (the alternative
investigation.md flagged as "arguably more correct"): (a) it would make this the only one of three
sibling wrapper-pattern migrations with resume semantics, an inconsistency with no ticket-level
requirement driving it — neither the ticket's Scope nor its ACs mention resuming suspended stabilize
projects; (b) `StrategicIntelligenceSystem.resume_project()`'s interaction with a `ProjectKind.STABILIZE`-
kind project has not been analyzed or test-covered by this ticket's own test_plan.md, so committing to
it as a side effect of enum-value choice (rather than a deliberate, separately-scoped, separately-tested
feature) would be exactly the kind of undocumented durable-state behavior CLAUDE.md's Hard Rules forbid
("Do not create hidden or implicit durable behavior"); (c) planning rules forbid planning more work than
ticket scope — a resume feature is a legitimate, separate future ticket, not something to smuggle in via
string choice. `test_region_stabilization_winner_preserves_dedup_lookup_inert_behavior` (Step 8)
documents this as an accepted, shared, unfixed gap, mirroring `test_social_contract_winner_preserves_
dedup_lookup_inert_behavior`'s precedent exactly.

**#5 — `should_pivot` pre-filter vs. `evaluate_project_switch()`'s own gate (investigation.md Risk #5).**
Chosen: **drop `should_pivot` entirely** — `RegionStabilizationGoalScorer.score()` emits a non-zero-
utility candidate whenever `region.hazard_level > 0.7` (via `compute_danger_urgency()`), with no
additional `urgency > profile.interruption_resistance` pre-filter, and lets
`evaluate_project_switch()`'s own retention-margin gate be the sole arbiter — consistent with every
other scorer in this epic (`AdventureGoalScorer`'s eligibility gate is cognition-profile support;
`SocialContractGoalScorer`'s is `ACTIVE` status + a valid kind mapping; neither has an urgency-threshold
pre-filter layered on top of simple eligibility). Rationale: `should_pivot`'s formula
(`urgency > profile.interruption_resistance`, a direct 0-1 vs. 0-1 comparison) and
`evaluate_project_switch()`'s `retention_margin = profile.interruption_resistance *
profile.resistance_multiplier` (a materially different formula over the same `interruption_resistance`
field, `intelligence.py:1003`, confirmed unchanged) are not interchangeable — keeping both would be
exactly the "conflate two different formulas" hazard investigation.md's own Anti-Drift Hazards warn
against. `profile.interruption_resistance` is not discarded by this choice: it still governs pivoting,
just through the single unified `retention_margin` mechanism every other tier-5 candidate already goes
through, rather than a redundant, differently-shaped pre-filter. **Disclosed behavior change**: some
entities that would/would not have pivoted under the old direct `urgency > interruption_resistance`
test may now behave differently under the new `retention_margin`-based gate — this is a real,
intentional consequence of unifying arbitration through one mechanism, not an oversight, and is called
out in Anti-Drift Notes and the parity ledger entry (Step 10).

**#6 — `STRAT-066`/`STRAT-131` opportunistic closure (Parity Ledger Overlap).** Chosen: **close both**,
not force-fit. Read directly (`docs/parity_ledger/strategic_cognition.yaml:698-709` and `:1422-1431`):
both entries' `text` fields literally name `test_strategic_pivot_on_regional_danger` and describe
"pivot on regional danger" — the exact subject this ticket's rewritten
`TestStrategicPivotOnDanger` tests (Step 9) verify, more rigorously than before (concern generation +
scorer output + real end-to-end materialization, not just a single method's direct-write side effect).
Both are `P0` with `test_path: null` today (CLAUDE.md-non-compliant independent of this ticket); this
ticket's own AC4 is a natural, not forced, opportunity to close both. They are near-duplicates of each
other (same test name, same subject, different ids) but this plan does not additionally deduplicate the
ledger itself (a separate governance action, out of this ticket's scope) — both get their own
`test_path` pointing at the same rewritten test, with a `divergence_note` cross-referencing the other.

## New Findings (beyond investigation.md's flagged questions, surfaced by this plan's own
fact-verification pass)

**#7 — Raw-score scale must be recalibrated from 100 to 2.9, or this ticket reproduces the
`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` defect class it exists to prevent a third
instance of.** The **original** `interpret_regional_danger()` set `stabilize_project.score =
urgency * 100` (`events.py:74`, pre-edit, confirmed read directly) — valid *only* because
`kind="stabilize"` was a bare string, so `_score_scale_max()`'s `isinstance(kind, ProjectKind)` check
(`intelligence.py:91-109`, confirmed unchanged) was `False`, falling through to the 100-ceiling
`_GOAL_UTILITY_SCORE_MAX`. Once this ticket's own AC1/AC5 land `ProjectKind.STABILIZE` and materialize
`ProjectState.kind=ProjectKind.STABILIZE`, that same `isinstance` check becomes `True`, reclassifying
any stabilize project onto the **2.9**-ceiling `_ADVENTURE_ROUTE_SCORE_MAX` instead. A raw score of
`urgency * 100` (up to 100) read back against a 2.9 denominator in `evaluate_project_switch()`'s
locked-branch (`candidate_pct = candidate_project.score / candidate_max`, `intelligence.py:1027`)
would produce percentages up to ~3448% — always trivially clearing both the normalized comparison and
the `0.8` urgency floor regardless of the current project's own strength, making a stabilize win
unconditional again by a different mechanism than the original bypass. **Fix (Step 3/4)**:
`compute_danger_urgency()` returns the unchanged `min(1.0, (hazard_level - 0.7) / 0.3)` urgency value
(0.0-1.0, byte-identical formula to the original); the scorer's raw score is
`urgency * _ADVENTURE_ROUTE_SCORE_MAX` (0.0-2.9), calibrated to the same ceiling `ADVENTURE_ROUTE`/
`SOCIAL_CONTRACT` already share (Design Decision precedent from ticket 5's own Design Decision #2 — do
not extend `_score_scale_max()`, calibrate the new raw-score formula to it instead). Algebraic check
(disclosed, not just asserted): `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) *
_GOAL_UTILITY_SCORE_MAX = (urgency * 2.9 / 2.9) * 100 = urgency * 100` — the tier-5 **utility** value
this scorer produces for arbitration purposes numerically reproduces the *original* `urgency * 100`
formula exactly; only the **committed `ProjectState.score`** (now `urgency * 2.9`, not `urgency * 100`)
changes, which is precisely the fix this recalibration exists to make.

**#8 — "Wins but stalls" defect, inherited from the original code, fixed as part of this migration
(same class the architecture-reviewer required a fix for in `TCK-20260811-ADVENTURE-GOAL-SCORER`, and
ticket 5's Design Decision #8 fixed for contracts).** `TacticalDecisionSystem._resolve_target_position()`
(`src/engine/tactical.py:702-753`, confirmed read directly) resolves `obj.target` only as an
int-castable resource-node/building id, or (via `ast.literal_eval`) a stringified coordinate tuple,
falling back to `obj.target_position` only if both parses fail. The **original**
`interpret_regional_danger()` set `ObjectiveState(target=region.id, ...)` with **no**
`target_position` — a region id like `"swamp"` is neither int-castable nor a coordinate-tuple string,
so `ast.literal_eval("swamp")` raises `SyntaxError` (caught, `target_pos` stays `None`), and with no
`target_position` fallback either, the objective was **never** tactically resolvable even when the
original bypass fired. **Fix (Step 4)**: `RegionStabilizationGoalScorer.score()` computes
`target_pos` as the region's centroid — `((region.bounds[0] + region.bounds[2]) / 2.0,
(region.bounds[1] + region.bounds[3]) / 2.0)` — mirroring the **exact same centroid formula** this
codebase already uses elsewhere for "a point representing a region" (`src/world/influence.py:90-93`,
confirmed read directly: `center = ((region.bounds[0] + region.bounds[2]) / 2, (region.bounds[1] +
region.bounds[3]) / 2)`, used there to place a stronghold at "Center of region"). This `target_pos`
flows into `GoalScore.target_pos` → Step 6's materialization branch's `ObjectiveState.target_position`
→ `_resolve_target_position()`'s node-3 fallback (`tactical.py:751-752`) — giving the materialized
stabilize objective real, resolvable navigation data for the first time, not merely preserving a
pre-existing (unreachable-in-production, but nonetheless real) defect.

**#9 — Shared-helper extraction, not duplication: `EventInterpreter.compute_danger_urgency()`.** To
satisfy the ticket's own Scope wording ("wrapping `EventInterpreter`'s existing unchanged internal
danger-interpretation logic") without literally two copies of the `hazard_level <= 0.7` /
`(hazard_level - 0.7) / 0.3` formula silently drifting apart over time, Step 3 extracts this pure
math into a new `EventInterpreter.compute_danger_urgency(region: RegionState) -> Optional[float]`
static method, called by both the simplified `interpret_regional_danger()` (for concern generation)
and `RegionStabilizationGoalScorer.score()` (for candidate scoring) — mirroring
`ContractService.get_project_mapping()`'s own extraction precedent from ticket 5 exactly (single
source of truth for logic two call sites both need).

**#10 — `lock_until_tick` convention: generic-branch default, not a bespoke preservation.** The
**original** `stabilize_project` construction (`events.py`, pre-edit) set **no** `lock_until_tick` at
all — it never went through `evaluate_project_switch()` in the first place (the bypass wrote
`current_project_id_set` directly), so there is no original lock *value* to preserve, unlike ticket
5's contracts (which had an explicit, preserved 50-tick lock). Chosen: Step 6's materialization branch
uses the tier-5 **generic** branch's own default, `min(current_tick + 10, current_tick + 50)` (==
`current_tick + 10`, `intelligence.py`'s `else:` branch, confirmed unchanged) — the same convention
every other `GoalKind` with no bespoke historical lock value already uses, rather than inventing a new
bespoke value with no original precedent to justify it.

**#11 — `proj_kind`/`obj_kind` travel through `GoalScore.metadata`, resolved once in the scorer — zero
new imports required in `intelligence.py`.** Mirrors ticket 5's `SOCIAL_CONTRACT` branch exactly
(`intelligence.py`'s current `elif` reads `best_candidate.metadata.get("proj_kind")`/`"obj_kind"`
without importing `ContractKind`/`ObjectiveKind` itself). `intelligence.py`'s current top-level import
of `src.core.strategic` (`intelligence.py:64-68`, confirmed read directly) does **not** include
`ObjectiveKind` — resolving `ObjectiveKind.INVESTIGATE` inside the new scorer module (which already
imports from `src.core.strategic`) and passing it through metadata avoids adding a new top-level
import to `intelligence.py` for this ticket, consistent with Step 6's "Do NOT touch" guard on
`intelligence.py`'s import block.

## Steps

### Step 1 — Add `ProjectKind.STABILIZE` enum member

**Files:** `src/core/strategic.py`

**Change:** In the `ProjectKind(str, Enum)` class body (confirmed exact current contents, read
directly, `strategic.py:143-156`: `CRAFTING, QUEST, EXPLORATION, COMBAT, SOCIAL, RECOVERY,
PREPARATION, TRAINING, HARVESTING, INFORMATION, INFORMATION_SEEKING, TRAVEL`), add one new member at
the end:
```python
    STABILIZE = "stabilize"  # Design Decision #2: matches the raw string interpret_regional_danger()
    # already used, mirrors DirectiveKind.STABILIZE's existing naming (strategic.py:89) -- a
    # different, unrelated enum class, no cross-validation, confirmed harmless (ProjectState.kind is
    # never assigned a DirectiveKind value anywhere in this codebase).
```

**Do NOT touch:** The 12 existing `ProjectKind` members. Do not touch `DirectiveKind`,
`ObjectiveKind`, `ConcernKind`, `BlockerKind` — read only, no edits (`ObjectiveKind.INVESTIGATE`
already exists and needs no change per Design Decision #2).

**Verify:** `test_project_kind_stabilize_is_registered_member`,
`test_stabilize_kind_value_does_not_collide_with_existing_project_kind_or_goal_kind` (Step 7).

---

### Step 2 — Add `GoalKind.REGION_STABILIZATION` enum member

**Files:** `src/core/strategic.py`

**Change:** In the `GoalKind(str, Enum)` class body (confirmed exact current contents, read directly,
`strategic.py:121-141`: 10 original members plus `ADVENTURE_ROUTE = "z_adventure_route"` and
`SOCIAL_CONTRACT = "social_contract"`), add one new member immediately after `SOCIAL_CONTRACT`'s
definition:
```python
    REGION_STABILIZATION = "region_stabilization"  # Design Decision #3: does not collide with any
    # existing GoalKind or ProjectKind value (in particular, deliberately NOT "stabilize" -- see
    # Design Decision #4's resume/dedup non-collision rationale). Sorts after "recover" (loses an
    # exact-utility tie to personal recovery) but before "resolve_blocker"/"social"/
    # "social_contract"/"town_return"/"z_adventure_route" (wins ties against a routine social
    # contract or adventuring) under intelligence.py:1408's
    # `sort(key=lambda x: (-x.utility, x.kind))` tie-break.
```

**Do NOT touch:** The 10 original members, `ADVENTURE_ROUTE`'s or `SOCIAL_CONTRACT`'s values
(confirmed unchanged). Do not touch `ProjectKind` in this step (Step 1's job).

**Verify:** `test_goal_kind_region_stabilization_is_registered_member`,
`test_region_stabilization_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind`,
`test_region_stabilization_goal_kind_value_does_not_break_existing_tie_break_ordering` (Step 7).

---

### Step 3 — Extract `EventInterpreter.compute_danger_urgency()`; simplify `interpret_regional_danger()`

**Files:** `src/systems/world_systems/events.py`

**Change (new helper):** Add a new static method, placed above `interpret_regional_danger()`:
```python
    @staticmethod
    def compute_danger_urgency(region: RegionState) -> Optional[float]:
        """
        LEG-RPG-116: pure hazard-threshold/urgency math, byte-identical to the original inline
        computation this method replaces (events.py, historical lines 48-51). Extracted so
        interpret_regional_danger()'s own concern generation and RegionStabilizationGoalScorer
        (src/ai/goals/region_stabilization_scorer.py) share a single source of truth for the
        threshold/formula -- see plan.md TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, New
        Finding #9, mirroring ContractService.get_project_mapping()'s own extraction precedent
        from TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER.

        Returns None if region.hazard_level <= 0.7 (no danger -- no concern, no candidate).
        Returns urgency in [0.0, 1.0] otherwise: 0.0 at hazard_level=0.7, 1.0 at hazard_level>=1.0.
        """
        if region.hazard_level <= 0.7:
            return None
        return min(1.0, (region.hazard_level - 0.7) / 0.3)
```

**Change (simplify `interpret_regional_danger()`):** Replace the current body (lines 36-102,
confirmed exact read directly above) with:
```python
    @staticmethod
    def interpret_regional_danger(
        entity: EntityState,
        region: RegionState,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
        """
        LEG-RPG-116: Strategic pivot on regional danger -- concern generation only.

        Project-pivot spawning is no longer performed here
        (TCK-20260811-REGION-STABILIZATION-GOAL-SCORER): RegionStabilizationGoalScorer
        (src/ai/goals/region_stabilization_scorer.py) now scores every entity's current region
        each tick as a tier-5 GoalRegistry candidate (via the shared
        EventInterpreter.compute_danger_urgency() helper), and the winning candidate is
        materialized into a real ProjectState/ObjectiveState by
        StrategicIntelligenceSystem.evaluate_strategic_intent()'s
        `elif best_candidate.kind == GoalKind.REGION_STABILIZATION:` branch, through
        evaluate_project_switch() -- not unconditionally. `entity` is retained as a parameter
        (unused by this simplified body) to preserve this method's existing call signature for
        its other 2 direct test call sites and for consistency with sibling
        EventInterpreter methods (interpret_scar_detection, interpret_near_death,
        interpret_directive_event all take `entity` as their first argument) -- see plan.md
        Scope Guards.
        """
        urgency = EventInterpreter.compute_danger_urgency(region)
        if urgency is None:
            return None

        concern = ConcernState(
            id=f"concern_danger_{region.id}",
            kind="danger",
            source=region.id,
            urgency=urgency,
            created_tick=current_tick
        )

        return StrategicUpdate(concerns_add_or_update=[concern])
```

**Other writers to `entity.strategic.current_project_id`/`entity.strategic.projects` this step must
not collide with (Fact-Verification Requirement #2):**
- `evaluate_project_switch()`'s three branches (`intelligence.py:985-1049`, confirmed unchanged) —
  the *only* writers that will ever again set `current_project_id_set` for a region-stabilize project
  after this step lands, reached solely via Step 6's new materialization branch, never via
  `interpret_regional_danger()` itself (which, per Design Decision #1, has no production caller
  either way).
- `src/systems/social_systems/contracts.py`'s `accept_contract()` (already simplified by ticket 5) —
  unrelated, structurally independent bypass site, unaffected.
- `interpret_near_death()` (`events.py`, line 179's `current_project_id_set=None` clear) — a
  different method in the same file; explicitly out of scope (a clear, not a steal); confirmed
  unaffected by this step's edit, which only touches `interpret_regional_danger()`'s own body.
- `interpret_scar_detection()` (`events.py`) — a different method; its own `"exploration"`/
  `"investigate"` raw strings already match real enum values and need no fix; confirmed unaffected.

**Do NOT touch:** `interpret_scar_detection()`, `interpret_near_death()`, `interpret_directive_event()`
(the other 3 `EventInterpreter` methods in this file — confirmed unrelated, unaffected). Do not remove
the `entity` parameter from `interpret_regional_danger()`'s signature even though the simplified body
no longer uses it (see docstring rationale above).

**Verify:** `test_no_pivot_when_hazard_low`, `test_concern_generated_on_high_hazard` (both existing,
must keep passing unmodified), `test_interpret_regional_danger_no_longer_sets_current_project_id_
directly` (new, AC2), `test_interpret_scar_detection_unaffected`, `test_interpret_near_death_unaffected`
(new anti-drift guards, Step 7).

---

### Step 4 — Create `RegionStabilizationGoalScorer` in a new module

**Files:** `src/ai/goals/region_stabilization_scorer.py` (new file)

**Change:** Create the file with the following structure (exact shape, not paraphrase):
```python
from __future__ import annotations
from typing import Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import GoalKind, ProjectKind, ObjectiveKind


class RegionStabilizationGoalScorer(GoalScorer):
    """
    GoalScorer wrapper around EventInterpreter.compute_danger_urgency() (src/systems/
    world_systems/events.py), registered under GoalKind.REGION_STABILIZATION as one candidate
    among many in tier 5 of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py). See plan.md
    TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, Design Decision #1: unlike
    SocialContractGoalScorer (live-reachable via an independent existing production writer),
    this scorer is the FIRST live-reachable path for LEG-RPG-116 (regional-danger-driven
    stabilization) -- interpret_regional_danger() itself has no production caller, before or
    after this ticket. Registering this scorer makes the mechanic live for the first time; this
    is a disclosed, intentional behavior-availability change, not a bypass-closure on an
    already-live path.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        from src.engine.legality import LegalityServiceV2

        # Same "entity's current region" resolution this codebase already uses in 7+ other call
        # sites (src/world/ecology.py, regional_sovereignty.py, boss.py, spawn.py, calamity.py,
        # influence.py, camp.py -- all read directly, confirmed identical call shape) -- not a
        # bespoke lookup invented for this scorer.
        region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
        if region is None:
            return GoalScore(kind=GoalKind.REGION_STABILIZATION, utility=0.0, target_id=None)

        from src.systems.world_systems.events import EventInterpreter

        urgency = EventInterpreter.compute_danger_urgency(region)
        if urgency is None:
            return GoalScore(kind=GoalKind.REGION_STABILIZATION, utility=0.0, target_id=None)

        # MUST be a lazy (function-local) import: mirrors AdventureGoalScorer's/
        # SocialContractGoalScorer's own documented reason -- intelligence.py's own top-level
        # `from src.ai.goals import GoalRegistry` creates a transitive module-load-order
        # dependency once this module is registered in src/ai/goals/__init__.py.
        from src.systems.strategic_systems.intelligence import (
            _ADVENTURE_ROUTE_SCORE_MAX,
            _GOAL_UTILITY_SCORE_MAX,
        )

        # New Finding #7: the ORIGINAL interpret_regional_danger() set
        # stabilize_project.score = urgency * 100 -- valid only while kind="stabilize" was a bare
        # string that fell through _score_scale_max()'s isinstance(kind, ProjectKind) check to
        # the 100-ceiling scale. Now that ProjectKind.STABILIZE is a real ProjectKind (AC1/AC5),
        # that check reclassifies the materialized project onto the 2.9-ceiling scale --
        # committing urgency*100 there would make it always trivially clear
        # evaluate_project_switch()'s lock-bypass gate, reproducing the
        # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class a third time.
        # Recalibrated to the SAME 0-2.9 ceiling ADVENTURE_ROUTE/SOCIAL_CONTRACT already share
        # (never modify _score_scale_max()/_ADVENTURE_ROUTE_SCORE_MAX itself -- see Scope Guards).
        raw_score = urgency * _ADVENTURE_ROUTE_SCORE_MAX
        utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX

        # New Finding #8: real target_pos (region centroid), fixing the ORIGINAL, inherited
        # "wins but stalls" defect -- TacticalDecisionSystem._resolve_target_position()
        # (tactical.py:702-753) can never resolve a bare region id string (not int-castable, not
        # a coordinate tuple) and the original ObjectiveState never set target_position either.
        # Centroid formula mirrors src/world/influence.py:90-93's own "Center of region"
        # precedent exactly.
        target_pos: Tuple[float, float] = (
            (region.bounds[0] + region.bounds[2]) / 2.0,
            (region.bounds[1] + region.bounds[3]) / 2.0,
        )

        return GoalScore(
            kind=GoalKind.REGION_STABILIZATION,
            utility=utility,
            target_id=region.id,
            target_pos=target_pos,
            metadata={
                "region_id": region.id,
                "raw_score": raw_score,
                # New Finding #11: proj_kind/obj_kind resolved HERE, not in intelligence.py --
                # keeps intelligence.py's materialization branch a "dumb" consumer needing zero
                # new top-level imports, mirroring SocialContractGoalScorer's identical pattern.
                "proj_kind": ProjectKind.STABILIZE,
                "obj_kind": ObjectiveKind.INVESTIGATE,
            },
        )
```

**Do NOT touch:** `src/systems/world_systems/events.py` beyond Step 3's edits — this scorer only
*calls* `EventInterpreter.compute_danger_urgency()`, it does not modify `events.py` further. Do not
add this class's logic to `src/ai/goals/scorers.py` — it lives in its own new file, mirroring
`adventure_scorer.py`'s/`social_contract_scorer.py`'s precedent (keeps the other 12 scorers' import
surface free of `src.systems.world_systems`/`src.engine.legality`).

**Verify:** `test_region_stabilization_goal_scorer_implements_goal_scorer_protocol`,
`test_region_stabilization_goal_scorer_metadata_carries_raw_score`,
`test_region_stabilization_goal_scorer_low_hazard_returns_zero_utility_no_target`,
`test_region_stabilization_goal_scorer_no_region_at_position_returns_zero_utility`,
`test_region_stabilization_target_pos_resolves_to_region_centroid` (all in
`tests/unit/ai/goals/test_region_stabilization_goal_scorer.py`, Step 7).

---

### Step 5 — Register `RegionStabilizationGoalScorer` in `src/ai/goals/__init__.py`

**Files:** `src/ai/goals/__init__.py`

**Change:** Confirmed current exact contents (read directly, 23 lines post-ticket-5: `GoalKind`,
`GoalRegistry`, `AdventureGoalScorer` import, `SocialContractGoalScorer` import, then 10 scorer
imports from `scorers.py`, then 12 `GoalRegistry.register(...)` calls). Add:
```python
from src.ai.goals.region_stabilization_scorer import RegionStabilizationGoalScorer
```
placed immediately after the existing `from src.ai.goals.social_contract_scorer import
SocialContractGoalScorer` line. Then add, after the existing
`GoalRegistry.register(GoalKind.SOCIAL_CONTRACT, SocialContractGoalScorer())` line:
```python
GoalRegistry.register(GoalKind.REGION_STABILIZATION, RegionStabilizationGoalScorer())
```

**Do NOT touch:** The 10 original scorer import/register lines, or `AdventureGoalScorer`'s/
`SocialContractGoalScorer`'s own import/register lines — order and content stay exactly as confirmed
read.

**Verify:** `test_goal_kind_region_stabilization_is_registered_member` (registry-side half:
`GoalRegistry._scorers[GoalKind.REGION_STABILIZATION]` is a `RegionStabilizationGoalScorer` instance),
`test_all_registered_scorers_are_canonical` (`tests/unit/strategic/test_enum_drift.py`, existing test,
must keep passing with a 13th member).

---

### Step 6 — Add the `REGION_STABILIZATION` materialization branch

**Files:** `src/systems/strategic_systems/intelligence.py`

**Change:** Confirmed current exact lines 1440-1516 (read directly, post-ticket-5): a three-way
`if best_candidate.kind == GoalKind.ADVENTURE_ROUTE: ... elif best_candidate.kind ==
GoalKind.SOCIAL_CONTRACT: ... else: ...` branch. Insert a new `elif` between `SOCIAL_CONTRACT`'s
branch and the generic `else:`:
```python
            elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:
                # ... UNCHANGED, not reproduced here ...
            elif best_candidate.kind == GoalKind.REGION_STABILIZATION:
                # AC2/AC3/AC5/AC6: materialize a regional-danger win into a real
                # ProjectKind-typed project, using proj_kind/obj_kind already resolved by
                # RegionStabilizationGoalScorer via EventInterpreter.compute_danger_urgency()
                # and carried in metadata -- intelligence.py needs no new import of
                # ObjectiveKind/EventInterpreter to build this branch (all resolved upstream in
                # the scorer, see plan.md New Finding #11).
                region_id = best_candidate.metadata.get("region_id")
                proj_kind = best_candidate.metadata.get("proj_kind")
                obj_kind = best_candidate.metadata.get("obj_kind")
                obj = ObjectiveState(
                    id=f"obj_stabilize_{region_id}_t{current_tick}",
                    kind=obj_kind,
                    target=best_candidate.target_id,
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE,
                )
                candidate_proj = ProjectState(
                    id=f"project_stabilize_{region_id}_t{current_tick}",
                    kind=proj_kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    # New Finding #10: the ORIGINAL bypass set no lock_until_tick at all (it
                    # never went through evaluate_project_switch()) -- no bespoke value to
                    # preserve, so this uses the SAME generic-branch default every other
                    # no-bespoke-lock GoalKind already gets, not a new invented value.
                    lock_until_tick=min(current_tick + 10, current_tick + 50),
                    created_tick=current_tick,
                    # NEVER best_candidate.utility -- see New Finding #7's full scale-mismatch
                    # analysis. utility is normalized onto the 100-ceiling scale for tier-5
                    # competition only; ProjectState.score is read back through
                    # _score_scale_max()'s 2.9-ceiling scale once kind is a real ProjectKind.
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
            else:
                # ... UNCHANGED, not reproduced here ...
```
Everything from the original `at_capacity = ...` line onward stays **unchanged** and continues to
reference `candidate_proj`/`obj`/`existing` as before — all four branches of the now-four-way `if`
produce those same two names, so the rest of the function needs no further edits.

**Other writers to `intelligence.py`'s materialization logic and `current_project_id` this step must
not collide with (Fact-Verification Requirement #2):**
- `if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:` / `elif ... GoalKind.SOCIAL_CONTRACT:` /
  the generic `else:` branches (same function, mutually exclusive per call since `best_candidate` is
  a single winner per tick) — no collision.
- `src/systems/social_systems/contracts.py`'s `accept_contract()` (already simplified by ticket 5) —
  no longer writes `current_project_id_set`/`projects_add_or_update` at all; unaffected.
- `src/systems/world_systems/events.py`'s `interpret_regional_danger()` (Step 3, this ticket) — no
  longer writes `current_project_id_set`/`projects_add_or_update` at all after Step 3 lands; the
  arbiter-materialized path (this step) becomes the *only* writer of a region-stabilize-originated
  `ProjectState`/`current_project_id`.
- `existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)`
  (`intelligence.py:1429`, unchanged) — confirmed (Design Decision #4) `best_candidate.kind` (always
  `GoalKind.REGION_STABILIZATION`, value `"region_stabilization"`) never string-equals
  `ProjectKind.STABILIZE`'s value (`"stabilize"`), so this lookup never matches for a
  `REGION_STABILIZATION` winner — the resume/dedup short-circuit never fires (inherited, shared gap
  with `ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`, deliberately not fixed here per Design Decision #4).

**Do NOT touch:** `evaluate_project_switch()`'s signature or internal lock logic
(`intelligence.py:955-1049`, confirmed unchanged) — this step only supplies a new
`candidate_project` into the existing, unmodified call. Do not touch the `existing`/resume-suspended-
project lookup at line 1429 (its inertness for `REGION_STABILIZATION` is accepted, not fixed here).
Do not add a new top-level import to `intelligence.py` — none is needed (confirmed:
`ProjectState`, `ProjectStatus`, `ObjectiveState`, `ObjectiveStatus`, `GoalKind`, `ProjectKind` are
already imported, `intelligence.py:64-68`; `ObjectiveKind` is deliberately NOT imported here — see
New Finding #11).

**Verify:** `test_region_stabilization_winner_materializes_with_raw_score_not_utility`,
`test_region_stabilization_materialized_kind_is_real_project_kind_enum_member`,
`test_active_region_stabilization_wins_arbitration_with_no_current_project`,
`test_high_lock_current_project_retains_against_low_urgency_regional_danger`,
`test_high_urgency_regional_danger_interrupts_locked_current_project`,
`test_region_stabilization_target_position_is_tactically_resolvable_not_a_stall` (all in
`tests/unit/strategic/test_region_stabilization_materialization.py`, Step 8).

---

### Step 7 — Unit tests for `RegionStabilizationGoalScorer` and enum drift guards

**Files:** `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py` (new file, same directory as
`test_adventure_goal_scorer.py`/`test_social_contract_goal_scorer.py`);
`tests/unit/strategic/test_enum_drift.py` (extended, not rewritten) or a new
`tests/unit/strategic/test_stabilize_enum.py` (Plan chooses: extend `test_enum_drift.py`, mirroring
where the `ProjectKind`/`GoalKind` collision-guard tests for tickets 1/5 already live, per
test_plan.md's own placement note)

**Change:**
- `test_project_kind_stabilize_is_registered_member` — asserts `ProjectKind.STABILIZE` exists with
  value `"stabilize"`.
- `test_goal_kind_region_stabilization_is_registered_member` — asserts `GoalKind.REGION_STABILIZATION`
  exists with value `"region_stabilization"`, and `GoalRegistry._scorers[GoalKind.REGION_STABILIZATION]`
  is a `RegionStabilizationGoalScorer` instance.
- `test_stabilize_kind_value_does_not_collide_with_existing_project_kind_or_goal_kind` — checks
  `ProjectKind.STABILIZE.value` against all other `ProjectKind`/`GoalKind` values for equality; asserts
  none match.
- `test_region_stabilization_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind` —
  checks `GoalKind.REGION_STABILIZATION.value` against all `ProjectKind`/`GoalKind` values, **including
  the new `ProjectKind.STABILIZE`**, for equality; asserts none match (direct regression guard for
  Design Decision #4's chosen non-collision).
- `test_region_stabilization_goal_kind_value_does_not_break_existing_tie_break_ordering` — asserts the
  new member's value does not change `ADVENTURE_ROUTE`'s or `SOCIAL_CONTRACT`'s existing relative sort
  position against the original 10 members (guards Design Decision #3's tie-break placement).
- `test_region_stabilization_goal_scorer_implements_goal_scorer_protocol` — same shape as the sibling
  tests for `AdventureGoalScorer`/`SocialContractGoalScorer`.
- `test_region_stabilization_goal_scorer_metadata_carries_raw_score` — asserts
  `set(score.metadata.keys()) == {"region_id", "raw_score", "proj_kind", "obj_kind"}` exactly
  (shape-exactness, mirroring the sibling tickets' style), and `metadata["proj_kind"] ==
  ProjectKind.STABILIZE`, `metadata["obj_kind"] == ObjectiveKind.INVESTIGATE`.
- `test_region_stabilization_goal_scorer_low_hazard_returns_zero_utility_no_target` — a region with
  `hazard_level <= 0.7` at the entity's position produces `GoalScore(utility=0.0, target_id=None)`,
  mirroring `test_no_pivot_when_hazard_low`'s semantics in scorer form.
- `test_region_stabilization_goal_scorer_no_region_at_position_returns_zero_utility` — entity
  positioned outside all declared regions (`LegalityServiceV2.get_region_for_position` returns `None`)
  produces `GoalScore(utility=0.0, target_id=None)`, not a crash.
- `test_region_stabilization_target_pos_resolves_to_region_centroid` — asserts
  `score.target_pos == ((region.bounds[0]+region.bounds[2])/2.0, (region.bounds[1]+region.bounds[3])/2.0)`
  for a region fixture with known bounds (direct regression guard for New Finding #8).
- `test_region_stabilization_goal_scorer_raw_score_calibrated_to_2_9_not_100` (new, direct regression
  guard for New Finding #7) — a region at `hazard_level = 1.0` (urgency = 1.0) asserts
  `metadata["raw_score"] == pytest.approx(2.9)`, **not** `100.0` — the single highest-value regression
  guard in this test file.

**Do NOT touch:** `tests/unit/ai/goals/test_adventure_goal_scorer.py`,
`tests/unit/ai/goals/test_social_contract_goal_scorer.py` — must keep passing unmodified, confirming
the two sibling scorers are undisturbed by adding a third sibling in the same package.

**Verify:** `pytest tests/unit/ai/goals/ tests/unit/strategic/test_enum_drift.py -v` passes; all tests
listed above pass.

---

### Step 8 — Integration tests for the materialization branch

**Files:** `tests/unit/strategic/test_region_stabilization_materialization.py` (new file)

**Change:**
- `test_region_stabilization_winner_materializes_with_raw_score_not_utility` — force a known raw score
  via a controlled high-hazard region fixture (e.g. `hazard_level=0.95` → `urgency ≈ 0.833` →
  `raw_score ≈ 2.417`, worked in the docstring), run `evaluate_strategic_intent(state, entity,
  force=True)` end-to-end, assert `ProjectState.score == pytest.approx(raw_score)` (not the normalized
  utility), plus a negative check (`project.score != utility_value`).
- `test_region_stabilization_materialized_kind_is_real_project_kind_enum_member` — asserts
  `project.kind == ProjectKind.STABILIZE` (the enum member, not the string `"stabilize"`) and
  `project.objectives[0].kind == ObjectiveKind.INVESTIGATE`.
- `test_active_region_stabilization_wins_arbitration_with_no_current_project` — entity has no current
  project, region at the entity's position has `hazard_level > 0.7`; assert `current_project_id`
  becomes the materialized project's id via `evaluate_project_switch()`'s unconditional-adopt path
  (`intelligence.py:985-998`).
- `test_high_lock_current_project_retains_against_low_urgency_regional_danger` — entity has a locked
  (`lock_until_tick > current_tick`), high-score current project plus a region just above the 0.7
  threshold (low urgency, e.g. `hazard_level=0.72`); assert `current_project_id` unchanged. Worked
  arithmetic in the docstring, mirroring `test_high_lock_current_project_retains_against_low_urgency_
  contract`'s existing style. Per ticket 5's own recorded Deviation #2 finding, confirm the fixture's
  HP/hostile-proximity does not accidentally trigger `_threat_resolved()`'s early lock-release
  (`intelligence.py`'s STRAT-236 check) — set HP below 80% or no hostile nearby as needed so the test
  actually exercises the intended lock-bypass gate, not an unrelated bypass.
- `test_high_urgency_regional_danger_interrupts_locked_current_project` — locked current project + a
  region near `hazard_level = 1.0` (urgency near 1.0, raw_score near the 2.9 ceiling); assert both
  `candidate_pct > normalized_effective_current_pct` and the `0.8` floor clear, and
  `current_project_id` switches to the materialized project. Per ticket 5's recorded Deviation #2, use
  a low `interruption_resistance` profile value if the default profile's `retention_margin` structurally
  prevents any 2.9-ceiling candidate from ever clearing the final raw `candidate.score >
  effective_current_score` check against the fixture's chosen current project.
- `test_region_stabilization_target_position_is_tactically_resolvable_not_a_stall` (direct proof of New
  Finding #8's fix) — after materialization, call `TacticalDecisionSystem._resolve_target_position(state,
  materialized_obj)` directly and assert it returns a non-`None` position equal to the region's
  centroid — via the `target_position` fallback (`tactical.py:751-752`), confirmed by also asserting
  `ast.literal_eval(obj.target)` does NOT succeed for the fixture's region id (i.e. the fallback path,
  not an accidental coordinate-string collision, is what resolves it).
- `test_region_stabilization_and_adventure_route_share_score_scale_as_designed` — asserts
  `_score_scale_max(ProjectKind.STABILIZE) == _ADVENTURE_ROUTE_SCORE_MAX`, explicit in-code assertion
  of the shared-scale design (mirrors the sibling tickets' own placeholder-test discipline).
- `test_region_stabilization_winner_preserves_dedup_lookup_inert_behavior` (direct regression guard for
  Design Decision #4) — confirms the pre-existing `existing = next(...)` lookup does not fire for a
  `REGION_STABILIZATION` winner (a suspended region-stabilize project is re-materialized fresh, not
  resumed) — documents the accepted, shared, unfixed gap rather than leaving it silently unasserted.

**Do NOT touch:** `tests/unit/strategic/test_adventure_route_materialization.py`,
`tests/unit/strategic/test_social_contract_materialization.py` — must keep passing unmodified, proving
the new `elif GoalKind.REGION_STABILIZATION:` branch is additive, not a restructure of the existing two
branches.

**Verify:** `pytest tests/unit/strategic/test_region_stabilization_materialization.py -v` passes.

---

### Step 9 — Rewrite `TestStrategicPivotOnDanger`'s two pivot tests

**Files:** `tests/unit/strategic/test_event_interpretation.py`

**Change:** Per the ticket's own AC4 ("pass against the new scorer path with equivalent assertions" —
not necessarily unchanged) and test_plan.md's prescribed shape, rewrite these two tests
(current bodies confirmed exact, read directly, lines 60-91):

- `test_project_pivot_when_urgency_exceeds_resistance` — equivalent assertions become: (1)
  `EventInterpreter.interpret_regional_danger()` still returns a concern (`urgency` computed via the
  shared helper) and no longer sets `current_project_id_set` (AC2 — assert `result.current_project_id_
  set is None` directly, plus `result.projects_add_or_update == []`, mirroring ticket 5's Anti-Drift
  Notes discipline of asserting the *absence* of any project write, not just the id-set field); (2)
  `RegionStabilizationGoalScorer().score(entity, state)` on an entity positioned inside a
  high-hazard region (`state.regions` fixture with the same hazard value) returns a non-zero-utility
  `GoalScore` whose `metadata["raw_score"]` is populated and calibrated to the 2.9 ceiling; (3)
  `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)` end-to-end
  produces a suspended `proj_craft` (same assertion as today) and a new active project whose id
  contains `"stabilize"` and whose `kind == ProjectKind.STABILIZE` (the enum member, not the string —
  the AC1/AC5 upgrade, mirroring ticket 5's Step 8 discipline for `ProjectKind.COMBAT`).
- `test_no_pivot_when_resistance_high` — equivalent assertions become: (1) concern still generated,
  `current_project_id_set is None` at the `interpret_regional_danger()` level (unchanged from today's
  outcome, now also true simply because the method never sets it at all per AC2, not only because
  resistance was high —**this semantic shift is called out explicitly in the test's own docstring**,
  per Design Decision #5's disclosed drop of the `should_pivot` pre-filter); (2) the scorer/arbiter
  path, when exercised end-to-end with a fixture whose region is just above the 0.7 threshold (low
  urgency, low raw_score) against a locked, comparably-strong current project, does **not** switch
  `current_project_id` away from `proj_craft` — asserted via `evaluate_strategic_intent()`, not by
  calling `interpret_regional_danger()` alone (since that method's own output no longer encodes the
  pivot decision at all).

**Do NOT touch:** `test_no_pivot_when_hazard_low`, `test_concern_generated_on_high_hazard` (same
class, untouched — Step 3 already confirmed these pass unmodified); `TestScarDetection` (both tests),
`TestDirectiveEvent` (all 3 tests), `TestNearDeath` (both tests) — all four other test classes in this
file, unrelated to this ticket's scope.

**Verify:** `pytest tests/unit/strategic/test_event_interpretation.py -v` passes, all tests in the file
green, including the 2 rewritten ones.

---

### Step 10 — Docs and parity ledger updates

**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`,
`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`

**Change (`04_strategic_cognition.md`, new subsection):** Confirmed by direct grep (investigation.md,
re-confirmed here) — zero existing coverage of LEG-RPG-116/regional danger/hazard-triggered
stabilization anywhere in this file. Add a new subsection, placed as **§2a** immediately after §2
("Interruption Resistance") and before §3 ("Strategic Memory: Leads & Blockers"):
```
## 2a. Regional Danger and Stabilization Projects (LEG-RPG-116)

When an entity's current region's `hazard_level` exceeds `0.7`, `EventInterpreter.
compute_danger_urgency()` (`src/systems/world_systems/events.py`) computes
`urgency = min(1.0, (hazard_level - 0.7) / 0.3)` (0.0 at the threshold, 1.0 at `hazard_level >= 1.0`)
and `interpret_regional_danger()` generates a `danger`-kind `ConcernState` from it every tick this
method is called (today: only from its own direct unit tests -- see the Reachability note below).

As of `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`, `RegionStabilizationGoalScorer`
(`src/ai/goals/region_stabilization_scorer.py`), registered under `GoalKind.REGION_STABILIZATION`,
is the live production path for this mechanic: it resolves the entity's current region via
`LegalityServiceV2.get_region_for_position()`, calls the same `compute_danger_urgency()` helper, and
-- if the region is dangerous -- emits a tier-5 `GoalScore` candidate. Its raw score is
`urgency * 2.9` (calibrated to System A's `~2.9` ceiling, §6.6), carried in `GoalScore.metadata
["raw_score"]`; its `target_pos` is the region's own centroid (`(bounds[0]+bounds[2])/2,
(bounds[1]+bounds[3])/2`), since a region id is not itself a resolvable tactical target. A winning
candidate materializes into a `ProjectState(kind=ProjectKind.STABILIZE, ...)` through
`evaluate_project_switch()`, exactly like every other tier-5 candidate -- not an unconditional
override.

**Reachability note**: `interpret_regional_danger()` itself has no production caller, before or
after this migration -- it exists only for its own concern-generation unit tests. Unlike
`AdventureGoalScorer`/`SocialContractGoalScorer` (which wrapped already-live decision paths),
`RegionStabilizationGoalScorer` re-implements the hazard-threshold/urgency decision to read
`state.regions` directly (via the shared `compute_danger_urgency()` helper), which means
**registering this scorer makes LEG-RPG-116 live-reachable in production for the first time** --
not merely a bypass-closure on an already-live mechanic. See
`docs/parity_ledger/strategic_cognition.yaml` (`STRAT-255`) for the full disclosure.

**Pre-migration behavior (historical, no longer current)**: prior to this ticket,
`interpret_regional_danger()` additionally computed `should_pivot = urgency >
profile.interruption_resistance` and, if true, unconditionally suspended the entity's current
project and set `current_project_id` directly -- with no comparison against the current project's
own strength or lock state. This direct-write bypass has been removed; `should_pivot`'s
urgency-vs-resistance formula is not preserved anywhere post-migration -- `profile.
interruption_resistance` still governs pivoting, but only through the single, unified
`retention_margin` mechanism (§2) every other tier-5 candidate already goes through.
```

**Change (§6.6 "Score Range Summary"):** Confirmed current exact text (read directly): a "third
consumer" paragraph already documents `SocialContractGoalScorer`'s reuse of
`_ADVENTURE_ROUTE_SCORE_MAX`. Add a fourth paragraph immediately after it:
```
The same constant has a fourth consumer as of `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`:
`RegionStabilizationGoalScorer` normalizes `urgency * _ADVENTURE_ROUTE_SCORE_MAX` (itself
recalibrated from the pre-migration `interpret_regional_danger()`'s `urgency * 100`, which was only
valid while `kind="stabilize"` was a bare string outside `_score_scale_max()`'s `ProjectKind`
classification -- see §2a's Reachability note) onto the same `GoalScore.utility` 0-100 scale via the
same `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` formula. This
constant is therefore now shared by three structurally unrelated raw-score domains (adventure
routing, social contracts, regional stabilization), purely because `_score_scale_max()` classifies
by Python enum class (`isinstance(kind, ProjectKind)`), not by provenance -- recorded in
`docs/parity_ledger/strategic_cognition.yaml` (`STRAT-255`).
```

**Change (`strategic_cognition.yaml`):**
1. Add a new entry `STRAT-255` (confirmed next available id — highest existing is `STRAT-254`,
   verified by direct grep of every `id: STRAT-` in the file, not assumed), mirroring `STRAT-254`'s
   structure: `text` describing `RegionStabilizationGoalScorer`'s landing, the
   `GoalKind.REGION_STABILIZATION = "region_stabilization"` value and its tie-break ordering, the
   `interpret_regional_danger()` simplification, and the explicit, un-softened disclosure that this
   ticket makes LEG-RPG-116 live-reachable for the first time (Design Decision #1) — `status:
   verified`, `priority: P2`, `v2_evidence` citing `src/ai/goals/region_stabilization_scorer.py`,
   `src/systems/world_systems/events.py` (the `compute_danger_urgency()` line range),
   `src/core/strategic.py` (both new enum-member lines), `src/ai/goals/__init__.py` (the register
   line), `src/systems/strategic_systems/intelligence.py` (the `elif` branch line range),
   `test_path` pointing at `tests/unit/strategic/test_region_stabilization_materialization.py`.
2. Update `STRAT-066` (`strategic_cognition.yaml:698-709`, confirmed `test_path: null` today) — set
   `test_path: tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_
   project_pivot_when_urgency_exceeds_resistance` per Design Decision #6. Do not change `status`
   (`legacy_verified`) or `text`.
3. Update `STRAT-131` (`strategic_cognition.yaml:1422-1431`, confirmed `test_path: null` today) — set
   the same `test_path` as `STRAT-066`, plus a `divergence_note`: `"Near-duplicate of STRAT-066 (same
   test name, same subject) -- both closed by the same rewritten test, not deduplicated in this
   ticket (out of scope)."` Do not change `status` or `text`.

**Change (design doc):** Confirmed (per investigation.md, re-confirmed by direct read,
`2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md:377-380` and `:493-497`) the
design doc's "Future Extension Patterns" section names `events.py:98` as "Status: still open," and its
`BYPASS` subgraph lists `EVT["world_systems/events.py:98 (stabilize_project)"]` as a still-unguarded
bypass writer. Update both to reflect this migration as done, mirroring the existing
`contracts.py:187` "Post-landing note" addendum pattern exactly (including the explicit
"this is a real, disclosed production behavior change, not merely a landed-but-inert wrapper"
framing that addendum already uses for `SocialContractGoalScorer` — this ticket's own version of that
disclosure is, if anything, stronger, since here there was no prior live path at all). Move `EVT` out
of the `BYPASS` subgraph in the diagram; the subgraph should retain only `TAC`/`GV` (the two
`clear`-only writers, unrelated to this ticket).

**Do NOT touch:** Any other section of `04_strategic_cognition.md` (§1, §3, §4, §5, §6.1-6.5,
§6.7-6.10 are unrelated). Do not touch `docs/parity_ledger/town_resource.yaml`, `progression.yaml`,
`world_dynamics.yaml`, or `social_narrative.yaml` — confirmed by investigation.md (re-confirmed here)
that no entry in any of these references `events.py`, `stabiliz`, or this bypass; this mechanic's
ledger home is `strategic_cognition.yaml` only.

**Verify:** No test verifies doc content directly; verified by inspection against the Authoritative
Mechanics Rule (CLAUDE.md) and by `docs-registry`/`frontmatter_valid` checks at Finalize.

---

### Step 11 — Run the full scoped regression suite

**Files:** none (verification-only step)

**Change:** Run:
```
pytest tests/unit/strategic/ tests/unit/ai/goals/ -v
```
This is the exact command test_plan.md specifies, covering: `test_event_interpretation.py` (direct
rewrite target), `test_enum_drift.py`, `test_score_normalization.py` (5 existing tests, must pass
unmodified — proves `_score_scale_max()`/the lock-bypass gate are untouched), the new
`test_region_stabilization_materialization.py`, `test_adventure_route_materialization.py`,
`test_social_contract_materialization.py`, `test_strategic_social_contracts.py`
(ticket 5's own rewrite target, untouched by this ticket), and `tests/unit/ai/goals/` (both existing
scorer test files plus the new `test_region_stabilization_goal_scorer.py`).

**Do NOT touch:** Never run `pytest tests/` (full suite) per CLAUDE.md's Testing Rule.

**Verify:** All listed suites green; no test in the regression surface required an edit to pass beyond
Steps 3 and 9's deliberate rewrites (if one did, that is itself a signal of unintended scope creep and
must be investigated before Finalize, not silently patched).

## Scope Guards

- **Do not wire `EventInterpreter.interpret_regional_danger()` into any production call site.** No
  such wiring ticket exists (confirmed by investigation.md). **This is not the same as claiming the
  whole mechanic stays inert** — see Design Decision #1: the scorer itself, once registered, is
  live-reachable via the same cadence-gated (`SystemCadence.strategic_intelligence`, default every 10
  ticks) and work-queue-budgeted (`StrategicWorkQueue.build()`) path every other tier-5 scorer already
  operates under — not "every tick for every entity" — because it re-implements the decision logic
  against `state.regions` directly rather than depending on `interpret_regional_danger()` being
  called. State this distinction explicitly wherever liveness is discussed.
- **Do not touch `interpret_scar_detection()`** (LEG-RPG-117, a separate method) or
  `interpret_near_death()`'s line-179 `current_project_id_set=None` clear (a clear, not a steal) —
  both explicitly out of scope per the ticket's own text, confirmed unaffected by Step 3's edit.
- **Do not touch `AdventureGoalScorer`/`SocialContractGoalScorer`, `src/domains/adventure/`, or
  `src/systems/social_systems/contracts.py`** — separate tickets' targets, structurally independent
  bypass sites.
- **Do not modify `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`, or `_GOAL_UTILITY_SCORE_MAX`.**
  This plan explicitly chose to calibrate the new raw-score formula to the existing 2.9 ceiling
  (New Finding #7), not to extend or change the shared constants/function themselves —
  `tests/unit/strategic/test_score_normalization.py`'s 5 existing tests must keep passing unmodified.
- **Do not use `best_candidate.utility` anywhere in Step 6's `ProjectState(score=...)` argument** —
  the single highest-value regression this ticket must not introduce (third instance of the same
  regression class both prior tickets in this epic also guarded against).
- **Do not deliberately collide `GoalKind.REGION_STABILIZATION`'s value with `ProjectKind.STABILIZE`'s
  value** (Design Decision #4) — the resume/dedup lookup's inertness for this kind is an accepted,
  shared gap, not something to silently "fix" via enum-value choice; a genuine resume feature is a
  separate, future, separately-tested ticket.
- **Do not re-add the `should_pivot`/`urgency > profile.interruption_resistance` gate anywhere** —
  Design Decision #5 deliberately drops it in favor of `evaluate_project_switch()`'s own
  `retention_margin` gate being the sole arbiter; re-adding it would reintroduce the "conflate two
  different formulas" hazard investigation.md's own Anti-Drift Hazards warn against.
- **Do not remove the `entity` parameter from `interpret_regional_danger()`'s signature** even though
  the simplified body no longer uses it — preserves the method's existing call signature and
  consistency with its 3 sibling `EventInterpreter` methods.
- **Do not skip New Finding #7's raw-score recalibration** (`urgency * 100` → `urgency *
  _ADVENTURE_ROUTE_SCORE_MAX`) — silently keeping `urgency * 100` while landing
  `ProjectKind.STABILIZE` would reproduce the `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-
  SCALE-BUG` defect class, the single highest-value regression risk in this entire ticket.
- **Do not skip New Finding #8's `target_pos` fix** — leaving the materialized objective's
  `target_position` unset would let a winning region-stabilization project lock the project slot but
  never let the entity navigate toward the region, reproducing the "wins but stalls" defect class the
  architecture-reviewer already required a fix for in `TCK-20260811-ADVENTURE-GOAL-SCORER`.
- **Do not widen `test_project_pivot_when_urgency_exceeds_resistance`/`test_no_pivot_when_resistance_
  high`'s assertions beyond what the new architecture actually produces** just to make them pass —
  AC4 requires "equivalent assertions," not "whatever assertions happen to pass."
- **Do not touch `docs/parity_ledger/town_resource.yaml`, `progression.yaml`, `world_dynamics.yaml`,
  or `social_narrative.yaml`** — this mechanic's ledger home is `strategic_cognition.yaml` only,
  confirmed by direct inspection.

## Dependency Map

- Step 1 (`ProjectKind.STABILIZE`) has no dependencies. Must land before Steps 4 and 6 (both
  reference it, directly or via metadata).
- Step 2 (`GoalKind.REGION_STABILIZATION`) has no dependencies. Must land before Steps 4, 5, and 6
  (all reference it).
- Step 3 (`compute_danger_urgency()` extraction + `interpret_regional_danger()` simplification) has no
  dependency on Steps 1/2 (does not reference either new enum member). Must land before Step 4 (the
  scorer imports `EventInterpreter.compute_danger_urgency()`).
- Step 4 (scorer) depends on Steps 1, 2, and 3.
- Step 5 (registration) depends on Step 4.
- Step 6 (materialization branch) depends on Step 2 and Step 4's `metadata` key names (`"region_id"`,
  `"proj_kind"`, `"obj_kind"`, `"raw_score"`) — not on Step 5 (reachable via direct
  `evaluate_strategic_intent()` calls in tests even before registration, though Step 8's integration
  tests are more naturally written after Step 5 lands so `GoalRegistry` picks up the scorer
  automatically).
- Step 7 (unit tests) depends on Steps 1-5.
- Step 8 (integration tests) depends on Steps 1-6.
- Step 9 (event-interpretation test rewrite) depends on Steps 3, 4, 6.
- Step 10 (docs/parity) depends on Steps 1-9 having landed (cites concrete line numbers/behavior that
  must already be true).
- Step 11 (regression run) depends on Steps 1-10 all landing.

No step depends on any ticket explicitly marked Out of Scope (`SocialContractGoalScorer`,
`AdventureGoalScorer`, their respective materialization paths).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| 1 — Missing enum-member gap resolved explicitly (`ProjectKind.STABILIZE` added) | Step 1 | `test_project_kind_stabilize_is_registered_member`, `test_stabilize_kind_value_does_not_collide_with_existing_project_kind_or_goal_kind` |
| 2 — `EventInterpreter.interpret_regional_danger()`'s stabilize-project path no longer sets `current_project_id_set` directly | Step 3 | `test_interpret_regional_danger_no_longer_sets_current_project_id_directly` |
| 3 — `RegionStabilizationGoalScorer` produces a comparable `GoalScore` that must clear `evaluate_project_switch()` to become `current_project_id` | Step 4, Step 6 | `test_region_stabilization_goal_scorer_implements_goal_scorer_protocol`, `test_active_region_stabilization_wins_arbitration_with_no_current_project` |
| 4 — `test_project_pivot_when_urgency_exceeds_resistance`/`test_no_pivot_when_resistance_high` pass against the new scorer path with equivalent assertions | Step 9 | Both tests, rewritten, in `tests/unit/strategic/test_event_interpretation.py` |
| 5 — Materialized `ProjectState.kind` uses a real `ProjectKind` enum member | Step 1, Step 4, Step 6 | `test_region_stabilization_materialized_kind_is_real_project_kind_enum_member` |
| 6 — Follows the same raw-score/utility separation requirement as `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER` | Step 4, Step 6 | `test_region_stabilization_winner_materializes_with_raw_score_not_utility`, `test_region_stabilization_goal_scorer_raw_score_calibrated_to_2_9_not_100` |

**AC2/AC5/AC6 cross-check (Fact-Verification Requirement #3, confirmed against Steps):** AC2 says
"no longer sets `current_project_id_set` directly" — Step 3's simplified `interpret_regional_danger()`
returns only `StrategicUpdate(concerns_add_or_update=[concern])`, never touching
`current_project_id_set` or `projects_add_or_update` at all — matches, stronger than merely omitting
one field. AC5 says "Materialized `ProjectState.kind` uses a real `ProjectKind` enum member" — Step 6's
branch sets `kind=proj_kind` where `proj_kind` is `ProjectKind.STABILIZE` (a real enum member, sourced
from Step 4's scorer metadata), never a bare string — matches. AC6 ("raw-score/utility separation") —
Step 6's branch sets `score=best_candidate.metadata.get("raw_score", 0.0)` verbatim, and Step 4's
scorer always populates `metadata["raw_score"]` with the **recalibrated** (2.9-ceiling, New Finding #7)
value, never the pre-migration `urgency * 100` value — matches, no contradiction found between the
ticket's stated field names/behavior and this plan's Steps.

## Anti-Drift Notes

- **New Finding #7's raw-score recalibration (`urgency * 100` → `urgency * _ADVENTURE_ROUTE_SCORE_MAX`)
  is the single highest-value regression to guard.** A regression here (keeping the original
  `urgency * 100` value while `ProjectKind.STABILIZE` reclassifies the project onto the 2.9-ceiling
  scale) silently reproduces the `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` defect
  class a third time — the resulting stabilize project would become trivially, unconditionally able to
  bypass any lock regardless of the current project's strength, functionally reintroducing the original
  unconditional-override bug through a different code path.
- **New Finding #8's target-position fix is inherited-bug remediation, not new-feature gold-plating —
  do not skip it as "out of scope."** Without a real `target_pos`, a region-stabilization project that
  wins tier-5 arbitration would lock the project slot but never let the entity navigate toward the
  region, silently reproducing the exact "wins but stalls" defect class the architecture-reviewer
  required a fix for in `TCK-20260811-ADVENTURE-GOAL-SCORER`. This was **not** flagged in
  investigation.md — a new finding from this plan's own fact-verification pass — but is squarely within
  this ticket's scope (it lives entirely inside the new scorer's own `target_pos` construction, the
  same sanctioned fix location the adventure and social-contract tickets' plans used).
- **Design Decision #1's reachability disclosure must not be softened anywhere it is repeated** — in
  the ticket's Implementation Notes, in `04_strategic_cognition.md`, and in the parity ledger entry
  alike, this must read as "this ticket makes LEG-RPG-116 live for the first time," never as "closes an
  arbiter bypass on an already-live mechanic" (that framing is true for ticket 5's contracts, not for
  this ticket).
- **Design Decision #4's non-collision choice is deliberate — do not "simplify" `GoalKind.
  REGION_STABILIZATION`'s value to `"stabilize"` during Implement even though it looks tidier** (it
  would literally equal `DirectiveKind.STABILIZE`'s and the new `ProjectKind.STABILIZE`'s string too).
  Doing so would silently activate the resume/dedup lookup for this kind only, an undocumented,
  untested behavior change relative to its two sibling migrations.
- **Design Decision #5's dropped `should_pivot` pre-filter is a real, disclosed behavior change** — do
  not treat `evaluate_project_switch()`'s `retention_margin` gate as merely "the same check under a
  different name." The two formulas can and will disagree on some entity/region combinations; this is
  accepted and intentional, not an oversight to reconcile.
- **`EventInterpreter.compute_danger_urgency()` (Step 3) is the single source of truth for the
  hazard-threshold/urgency formula** — both `interpret_regional_danger()`'s concern generation and
  `RegionStabilizationGoalScorer.score()`'s candidate scoring must derive from it. Do not let a future
  edit hardcode `hazard_level <= 0.7` / `(hazard_level - 0.7) / 0.3` a second time anywhere else — that
  would reintroduce the exact "two sources of truth can drift" risk this extraction was designed to
  prevent.
- **`lock_until_tick=min(current_tick+10, current_tick+50)` in Step 6 is deliberately the generic
  branch's default, not a bespoke preservation** (New Finding #10, unlike ticket 5's deliberate 50-tick
  contract-specific preservation) — do not "correct" this to some other value during Implement without
  re-reading New Finding #10's rationale first; there is no original lock value this ticket is trying
  to preserve.
- **Docs**: `docs/mechanics/04_strategic_cognition.md` §2a (new) and §6.6 (fourth-consumer paragraph),
  `docs/parity_ledger/strategic_cognition.yaml` (new `STRAT-255`, plus `STRAT-066`'s and `STRAT-131`'s
  `test_path` updates), and the design doc's "Future Extension Patterns"/`BYPASS` subgraph (Step 10)
  must not be silently skipped — this ticket's own Docs Requiring Update depends on all landing in the
  same session per CLAUDE.md's Authoritative Mechanics Rule.
