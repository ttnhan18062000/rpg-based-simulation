---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
artifact_type: investigation
tags: [cognition, world]
---

# Investigation — TCK-20260811-REGION-STABILIZATION-GOAL-SCORER

## Current Behavior

### `src/systems/world_systems/events.py` — `EventInterpreter.interpret_regional_danger()` (exact bypass site confirmed)

Full method at lines 35-102. Exact sequence:

```python
36: def interpret_regional_danger(entity, region, current_tick) -> Optional[StrategicUpdate]:
48:     if region.hazard_level <= 0.7: return None
51:     urgency = min(1.0, (region.hazard_level - 0.7) / 0.3)
54-60:  concern = ConcernState(kind="danger", source=region.id, urgency=urgency, ...)
63-64:  profile = entity.strategic.profile
        should_pivot = urgency > profile.interruption_resistance
66-68:  updates = StrategicUpdate(concerns_add_or_update=[concern])
70:     if should_pivot and entity.strategic.current_project_id:
72-87:      stabilize_project = ProjectState(
                id=f"project_stabilize_{region.id}", kind="stabilize", status=ACTIVE,
                score=urgency * 100,
                objectives=[ObjectiveState(id=f"obj_stabilize_{region.id}", kind="investigate",
                                            target=region.id, status=ACTIVE)],
                active_objective_id=f"obj_stabilize_{region.id}", created_tick=current_tick)
89-93:      # suspend current project (unconditional, no arbiter check)
95-100:     updates = replace(updates,
                projects_add_or_update=[stabilize_project] + suspended,
                current_project_id_set=stabilize_project.id,   # <-- THE BYPASS
                current_objective_id_set=stabilize_project.active_objective_id)
102:    return updates
```

**Line 98's `current_project_id_set=stabilize_project.id`** (the ticket's cited "events.py:98
stabilize_project") is exactly this assignment — confirmed, not approximate. It runs whenever
`should_pivot` is true (`urgency > interruption_resistance`) **and** the entity already has a
current project — unconditionally, with no `evaluate_project_switch()` call anywhere in this
method. Unlike the sibling `SOCIAL_CONTRACT` ticket's bypass (an `if`-gated single write), this
gate is the *only* gate — there is no lock check, no score comparison against the current
project's retention margin, nothing. `urgency * profile.interruption_resistance` is the sole
condition; once satisfied, the pivot always wins regardless of how strong or how recently-locked
the current project is.

`should_pivot` itself is a **pre-normalized comparison already baked into `interpret_regional_danger()`**:
`urgency` (0.0-1.0) vs. `profile.interruption_resistance` (0.0-1.0, `CognitionProfile.interruption_resistance`,
default 0.3, `strategic.py:328`). This is a *different* interruption-resistance check than
`evaluate_project_switch()`'s own `retention_margin = profile.interruption_resistance * profile.resistance_multiplier`
— the two are not the same formula and must not be conflated. Whether `should_pivot`'s own gate
should be kept as a pre-filter (only entities whose personal resistance is already overcome even
generate a candidate) or dropped in favor of letting `evaluate_project_switch()` be the sole
arbiter is a real design question — flagged in Risks.

### `EventInterpreter.interpret_regional_danger()` has **no production caller anywhere in `src/`** (confirmed, not assumed)

```
grep -rn "interpret_regional_danger\|EventInterpreter" src/ tests/ --include=*.py
  src/systems/event_interpreter.py:1: from src.systems.world_systems.events import EventInterpreter
  src/systems/event_interpreter.py:2: __all__ = ["EventInterpreter"]
  tests/unit/strategic/test_event_interpretation.py: 5 call sites (all 4 EventInterpreter methods)
```
`graphify query "EventInterpreter production call site"` corroborates: only 2 nodes reference
`EventInterpreter` as a `Call` target codebase-wide, both in unrelated test files (a false-positive
generic `Call` node match, not real references). `src/systems/event_interpreter.py` is a pure
re-export shim (2 lines) — nothing imports *it* either, outside the test file, which imports
`EventInterpreter` from it directly.

**This is a materially different reachability situation than `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`.**
That ticket's `accept_contract()` also had no direct caller, but the *scorer itself* was confirmed
live-reachable in production because `entity.strategic.contracts` — the state the scorer reads —
is populated by a real production path (`CoreActions.execute_recruit()`) independent of
`accept_contract()`. Here, there is no analogous independent production writer of
`entity.strategic.current_project_id`/`entity.strategic.projects` that a `RegionStabilizationGoalScorer`
could read from instead: the *entire* danger→stabilize decision logic (hazard threshold check,
urgency computation, concern generation, stabilize-project construction) lives inside
`interpret_regional_danger()` itself, which nothing calls. Unless the new scorer's `score()` method
re-implements this decision logic inline against `region: RegionState` state it reads directly from
`AuthoritativeState` (i.e. `state.regions`), **there is no live path today by which a
`RegionStabilizationGoalScorer` could produce a non-zero score in a real simulation tick** — the
entire mechanic (LEG-RPG-116) is currently dead code in production, exercised only by
`tests/unit/strategic/test_event_interpretation.py`. This must be disclosed explicitly, not silently
carried forward as if it mirrors ticket 5's disclosed-but-still-live framing. See Risks #1.

### `src/core/strategic.py` — enum state (confirmed exact, post ticket-5)

```python
85:  class DirectiveKind(str, Enum):
         AVENGE, EXPLORE, STABILIZE = "stabilize", ACQUIRE, PROTECT, COMBAT
104: class ObjectiveKind(str, Enum):
         REACH_LOCATION, ACQUIRE_ITEM, DEFEAT_ENEMY, INVESTIGATE = "investigate", REACH_SERVICE,
         ASK_INFORMATION, BUY_ITEM, REQUEST_CRAFT, REACH_RESOURCE, HARVEST_RESOURCE, ACCEPT_QUEST,
         REST, RETURN_TOWN
121: class GoalKind(str, Enum):
         HARVESTING ... GUILD (10 originals), ADVENTURE_ROUTE = "z_adventure_route",
         SOCIAL_CONTRACT = "social_contract"   (12 members today)
143: class ProjectKind(str, Enum):
         CRAFTING, QUEST, EXPLORATION, COMBAT, SOCIAL, RECOVERY, PREPARATION, TRAINING,
         HARVESTING, INFORMATION, INFORMATION_SEEKING, TRAVEL   (12 members today)
```

**Correction to the ticket's own Assumptions text, confirmed by direct read — narrower gap than
stated.** The ticket's Assumptions bullet says "events.py's stabilize/exploration/investigate
project/objective kinds are currently raw strings with no matching ProjectKind/ObjectiveKind enum
member." Checked all three against the enums above:
- `kind="stabilize"` (`ProjectState`, `interpret_regional_danger()`, line 74) — **confirmed missing**,
  no `ProjectKind` member has value `"stabilize"`. This is the one real gap in this ticket's scope.
- `kind="investigate"` (`ObjectiveState`, `interpret_regional_danger()` line 80, **and**
  `interpret_scar_detection()` line 129) — **already matches** `ObjectiveKind.INVESTIGATE = "investigate"`
  exactly. Not a gap; the raw string happens to already coincide with a real enum value (frozen
  dataclasses with no runtime type validation mean the raw string "works" today by coincidence, but
  it is not classified as `ObjectiveKind` by any `isinstance` check — only `_score_scale_max()`'s
  `isinstance(kind, ProjectKind)` check on `ProjectState.kind` matters for the scale-selection defect
  class; there is no analogous `isinstance(kind, ObjectiveKind)` check anywhere in the codebase today
  that this could silently misroute).
- `kind="exploration"` (`ProjectState`, `interpret_scar_detection()`, line 122) — **already matches**
  `ProjectKind.EXPLORATION = "exploration"` exactly. Also not a gap — and also **out of this ticket's
  scope entirely**: `interpret_scar_detection()` is a separate method (LEG-RPG-117, scar detection),
  not named anywhere in this ticket's Scope/AC text, which is scoped strictly to
  `interpret_regional_danger()`'s stabilize-project path.

**Net finding for Plan**: only `ProjectKind.STABILIZE` needs to be added (or an existing member
explicitly justified as reuse — see Risks #2 for why `STABILIZE` is the clean choice, not e.g.
`ProjectKind.RECOVERY` or `ProjectKind.COMBAT`). No `ObjectiveKind` addition is required — the
objective already carries a real enum value's string, though it is stored as a bare `str`, not
literally `ObjectiveKind.INVESTIGATE` (a materialization-time upgrade, mirroring ticket 5's Step 8
"uses the enum member, not just the string" upgrade, worth doing but not independently AC-required
here beyond the `ProjectState.kind` AC).

`DirectiveKind.STABILIZE = "stabilize"` (`strategic.py:89`) already exists and is unrelated —
`DirectiveKind` and `ProjectKind` are different enum classes with no cross-validation; a new
`ProjectKind.STABILIZE = "stabilize"` would share a string value with `DirectiveKind.STABILIZE` but
not collide (different classes, `_score_scale_max()` and the `existing = next(...)` dedup lookup
both key off the *bound* enum class members `p.kind`/`best_candidate.kind` are actually assigned
to at construction time — `ProjectState.kind` is never assigned a `DirectiveKind` value anywhere in
this codebase, confirmed by the `ProjectState`/`DirectiveState` dataclass definitions being entirely
separate).

### `_score_scale_max()` (`intelligence.py:91-109`) — same constraint ticket 5 already worked through, re-confirmed applicable here

```python
def _score_scale_max(kind) -> float:
    if isinstance(kind, ProjectKind):
        return _ADVENTURE_ROUTE_SCORE_MAX   # 2.9
    return _GOAL_UTILITY_SCORE_MAX          # 100.0
```
Once `ProjectState.kind` for a materialized stabilize project is a real `ProjectKind.STABILIZE`
member, it is classified onto the same 2.9-ceiling scale `ADVENTURE_ROUTE` and `SOCIAL_CONTRACT`
already share. Ticket 5's Design Decision #2 already resolved the "share vs. extend
`_score_scale_max()`" question in favor of sharing (not extending) — that decision's rationale
(no provenance field on `ProjectState`, avoids a durable-state-model change) applies identically
here; there is no new fact that would justify re-opening it for this ticket. **`_score_scale_max()`
itself needs no code change** — flagged in the ticket's own prompt as an open question, resolved by
direct inheritance of ticket 5's precedent, not a new investigation finding.

### `evaluate_project_switch()` (`intelligence.py:955-1049`) — confirmed mechanically achievable, same three paths as ticket 5

- No current project / current not ACTIVE (985-998): unconditional adopt.
- Current locked (1005-1037): bypass requires `candidate_pct > normalized_effective_current_pct AND
  candidate_pct > 0.8`, `candidate_pct = candidate_project.score / _score_scale_max(candidate_project.kind)`.
  Once `candidate_project.kind` is `ProjectKind.STABILIZE`, this uses the 2.9 ceiling — the new
  raw-score formula must be calibrated against 2.9 for this comparison to behave sensibly, exactly
  the same calibration constraint ticket 5's Design Decision #3 already solved for contracts.
- Current unlocked (1039-1047): raw `candidate_project.score > effective_current_score` comparison,
  unaffected by scale choice.

No changes needed to `evaluate_project_switch()` itself — confirmed unchanged code, same as ticket 5.

### Materialization branch (`intelligence.py:1428-1523`) — confirmed exact shape, new branch required

Current three-way structure: `if best_candidate.kind == GoalKind.ADVENTURE_ROUTE: ... elif
best_candidate.kind == GoalKind.SOCIAL_CONTRACT: ... else: ...` (generic branch, 10 original
`GoalKind`s). A new `elif best_candidate.kind == GoalKind.<REGION_STABILIZATION_NAME>:` branch is
required between the `SOCIAL_CONTRACT` branch and the generic `else:`, mirroring their shape:
build `ProjectState`/`ObjectiveState` from `best_candidate.metadata`, `score=best_candidate.metadata.get("raw_score", 0.0)`
— never `best_candidate.utility` (identical Anti-Drift rule, third repetition of the same class of
bug `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` fixed).

The `existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)`
dedup/resume lookup at line 1429 has the same non-collision property discipline ticket 5 documented:
the new `GoalKind` value must not string-collide with any `ProjectKind` value (in particular must not
be `"stabilize"` itself, since `ProjectKind.STABILIZE` will also be `"stabilize"` — picking
`GoalKind.STABILIZE = "stabilize"` verbatim would make this lookup **always match** any suspended
stabilize project, which is arguably *desirable* here — unlike `ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`,
where the inert dedup was accepted as a shared gap, a colliding `GoalKind` value would actually
*fix* the resume gap for this one kind specifically. This is a genuine design fork, not
inherited from ticket 5's precedent — flagged in Risks #4, must not be decided implicitly.

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md`**: contains **no** section on LEG-RPG-116, regional
  danger, hazard-triggered stabilization, or `interrupt_resistance`-vs-`urgency` pivoting anywhere
  (confirmed by direct grep — zero hits for "LEG-RPG-116", "stabiliz", "regional danger",
  "hazard_level"). §2 ("Generalized Bypass") and §6.6 ("Score Range Summary") — the two sections
  ticket 5 flagged as needing updates for `SOCIAL_CONTRACT` — also say nothing about this mechanic.
  This is a genuine, pre-existing doc gap, not introduced by this ticket, but this ticket's own
  migration is the natural point to close it (a new tier-5 candidate kind's raw-score range needs
  documenting in §6.6 alongside `ADVENTURE_ROUTE`'s and `SOCIAL_CONTRACT`'s, once Plan picks a
  formula/ceiling).
- **Durable State Rule (CLAUDE.md)**: `GoalScore.metadata` is intra-tick only — same reasoning as
  both prior tickets in this epic. What's committed into `ProjectState`/`ObjectiveState` via the
  arbiter is the durable surface that must stay on the correct scale.

## Docs Requiring Update

- `docs/parity_ledger/strategic_cognition.yaml`: two existing P0 entries directly describe this exact
  mechanic and both currently have `test_path: null` (see Parity Ledger Overlap) — both need their
  `v2_evidence`/`test_path` updated once the rewritten tests land, plus a new `STRAT-25X`-style entry
  (mirroring `STRAT-254`) documenting the `RegionStabilizationGoalScorer` landing itself.
- `docs/mechanics/04_strategic_cognition.md`: needs a new subsection describing LEG-RPG-116 (currently
  entirely undocumented) and an addition to whatever section documents tier-5 raw-score ranges (§6.6
  per ticket 5's precedent), once Plan picks a formula/ceiling for the new scorer.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: its own
  "Future Extension Patterns" section (lines 377-380) names `events.py:98` as "Status: still open" and
  its `BYPASS` subgraph (lines 493-497) lists `EVT["world_systems/events.py:98 (stabilize_project)"]`
  as a still-unguarded bypass writer — both go stale the moment this ticket lands and need a
  "Post-landing note" addendum mirroring the one already added for `contracts.py:187` (lines 386-396).

## Parity Ledger Overlap

- **STRAT-066** (P0, `strategic_cognition.yaml:698-709`, `status: legacy_verified`, `test_path: null`):
  "`test_strategic_pivot_on_regional_danger`: Strategic pivot on regional danger — Verify that heroes
  pivot from personal quests to regional stabilization during high-danger events." Directly this
  ticket's subject matter.
- **STRAT-131** (P0, `strategic_cognition.yaml:1422-1431`, `status: legacy_verified`, `test_path: null`):
  "`test_strategic_pivot_on_regional_danger`: pivot on regional danger." **A near-duplicate of
  STRAT-066** (same referenced test name, same subject, different id) — both P0, both currently
  ungated by any real `test_path`. Both are natural closure candidates for this ticket's rewritten
  `tests/unit/strategic/test_event_interpretation.py` tests, mirroring ticket 5's `SOC-208` closure
  discipline — Plan should decide whether to close both, dedupe them, or close one and cross-reference
  the other; not decided here.
- Per CLAUDE.md, **P0 entries require a passing `test_path`** — both are currently non-compliant
  (`test_path: null`) independent of this ticket; this ticket's own AC (re-running
  `test_project_pivot_when_urgency_exceeds_resistance`/`test_no_pivot_when_resistance_high` "with
  equivalent assertions") is a natural, not forced, opportunity to finally close this gap for both
  entries — confirmed no other existing ticket already claims this closure.
- No entry in `docs/parity_ledger/world_dynamics.yaml` references `events.py`, `stabiliz`, or this
  bypass — checked directly per the task's instruction to verify, not assume; the mechanic's
  ledger home is `strategic_cognition.yaml` only (the `hazard_level`/`hazard_kind` entries in
  `world_dynamics.yaml` around lines 286-347 cover `EnvironmentService`'s HP/Readiness drain
  mechanic, a different, unrelated hazard-consequence pipeline that also reads `region.hazard_level`
  but has no relationship to strategic project pivoting).

## Prior Work

- **`TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`** (done, `stored_artifacts/`): the direct structural
  precedent — this ticket's investigation reuses its resolved design decisions wherever the facts are
  identical (file layout: new co-located scorer module under `src/ai/goals/`, not `scorers.py`;
  `_score_scale_max()` share-not-extend decision; never-`.utility`-in-materialization rule;
  metadata-carries-raw-score convention) and flags where the facts genuinely differ (reachability —
  see Risks #1; the resume/dedup collision question — see Risks #4).
- **`TCK-20260811-ADVENTURE-GOAL-SCORER`** (done): the wrapper pattern's origin.
- **`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`**: landed `_score_scale_max()`,
  `_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX`, and the normalized-percentage lock-bypass
  gate this ticket's stabilize candidates will flow through unchanged.
- **`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`**: fixed the `retention_margin`
  normalization-denominator bug — already fixed generically, applies automatically to any
  stabilize-originated locked project too.
- **`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`**: names
  this exact ticket's target explicitly (`events.py:98` → `RegionStabilizationGoalScorer`, "Status:
  still open", `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER` cited by id) — confirms this is a
  specifically-anticipated, not speculative, follow-on, and that the design doc's own author expected
  exactly this ticket to eventually land it.

## Risks and Open Questions

1. **Reachability — genuinely different from ticket 5, top priority for Plan.** `interpret_regional_danger()`
   has no production caller, and unlike `SocialContractGoalScorer` (which reads `entity.strategic.contracts`,
   independently populated by a live path), there is no independent live writer of the state this
   mechanic depends on. A `RegionStabilizationGoalScorer.score()` that merely reads
   `entity.strategic.projects`/`current_project_id` cannot reproduce the hazard-threshold-crossing
   decision — it would need to read `region.hazard_level` directly from `AuthoritativeState.regions`
   and **re-implement** the threshold/urgency logic inline (a genuine duplication or a refactor that
   extracts `interpret_regional_danger()`'s pure-decision math into a shared helper the scorer also
   calls). Neither approach is prescribed by the ticket's Scope text, and the ticket's Assumptions
   section's claim ("today stabilize always wins the project slot, post-migration it competes and
   can lose") is only true for the **unit-test-exercised** call path, not any live simulation tick —
   this must be stated explicitly and not silently conflated with ticket 5's genuinely-live-production
   framing. Plan must decide: (a) scorer duplicates/extracts the region-danger decision logic and
   reads `state.regions` directly (making the mechanic live-reachable for the first time, a larger,
   disclosed behavior-availability change), or (b) scorer wraps `EventInterpreter.interpret_regional_danger()`
   itself somehow (awkward — that method's signature takes a single `region`, not the full `state`,
   and returns a `StrategicUpdate`, not a `GoalScore`, and currently synthesizes the winning project
   inline rather than just scoring a candidate), or (c) land the wrapper unit-test-correct only,
   explicitly disclosing (like ticket 5 did for `accept_contract()` alone, but more starkly since
   *nothing* here is currently live) that this closes the architecture gap without creating new live
   behavior. **Not resolved here — blocks Plan's Step 3 design.**

2. **`ProjectKind.STABILIZE` vs. reusing an existing member.** `STABILIZE` is the clean choice:
   matches the raw string already in use (`"stabilize"`), mirrors `DirectiveKind.STABILIZE`'s existing
   naming, has no collision with any current `ProjectKind`/`GoalKind` value. Reusing e.g.
   `ProjectKind.RECOVERY` or `ProjectKind.COMBAT` (as ticket 5 did for contracts, where no dedicated
   member existed and reuse was deliberately chosen to avoid enum growth) would be a worse fit here —
   "stabilize a dangerous region" is not really "recover" (personal HP/fatigue recovery, per
   `ProjectKind.RECOVERY`'s existing usage) or "combat" (a specific engagement, not a region-wide
   crisis response) semantically. Recommend adding the new member; Plan should confirm/record this
   explicitly per the ticket's own AC wording ("or an existing member reused with explicit rationale
   recorded").

3. **New `GoalKind` member name and tie-break value, not resolved here.** Following the `ADVENTURE_ROUTE`/
   `SOCIAL_CONTRACT` precedent, a new member (candidate name: `GoalKind.REGION_STABILIZATION` or
   `GoalKind.STABILIZATION`) is needed. Its value must (a) not collide with any of the 12 existing
   `GoalKind` values or any `ProjectKind` value (`"stabilize"` itself is available as a `GoalKind`
   value with no `GoalKind` collision, but **would** collide with the new `ProjectKind.STABILIZE`
   string — see Risks #4 below for why that specific collision is a live design fork, not
   automatically bad), and (b) have a deliberately-chosen ordering relative to `ADVENTURE_ROUTE`
   (`"z_adventure_route"`) and `SOCIAL_CONTRACT` (`"social_contract"`) on an exact-utility tie — does
   region-crisis urgency deserve to out-rank an accepted social obligation and routine adventuring?
   Qualitatively yes (a >0.7 hazard_level crisis is more urgent than routine adventuring or a
   contract's ongoing standing), suggesting a value that sorts before both, but this is a genuine
   semantic call for Plan, not mechanical.

4. **Resume/dedup lookup collision — a genuine, non-inherited design fork.** Ticket 5 treated the
   `existing = next(... p.kind == best_candidate.kind ...)` non-match as an accepted, shared,
   out-of-scope gap for both `ADVENTURE_ROUTE` and `SOCIAL_CONTRACT`, deliberately choosing
   non-colliding `GoalKind` values to keep behavior identical to before. Here, if `GoalKind`'s new
   member value is chosen to literally equal `"stabilize"` (matching `ProjectKind.STABILIZE`'s
   string), the lookup **would** match a suspended stabilize project and actually resume it instead
   of re-materializing fresh — arguably the *more correct* behavior for a recurring regional crisis
   (the same region's danger recurring should resume its own suspended stabilize effort, not spawn a
   new one every time). This is a real, un-inherited design choice Plan must make explicitly, not by
   accident of whatever `GoalKind` value happens to get picked in Risk #3.

5. **`should_pivot`'s pre-filter vs. `evaluate_project_switch()`'s own gate — potential double-gating.**
   `interpret_regional_danger()`'s `should_pivot = urgency > profile.interruption_resistance` check is
   a *different* formula than `evaluate_project_switch()`'s `retention_margin`-based gate. If the new
   scorer's `score()` re-implements the region-danger decision (per Risks #1's option (a)) and still
   applies `should_pivot` as a pre-filter before returning a non-zero-utility `GoalScore`, low-urgency
   candidates that would otherwise still be visible to `evaluate_project_switch()`'s own comparison
   get filtered out one step earlier, potentially double-gating in a way `ADVENTURE_ROUTE`/
   `SOCIAL_CONTRACT` do not (neither has an analogous pre-filter beyond simple eligibility checks —
   `AdventureGoalScorer`'s `_supports_adventure_routing` and `SocialContractGoalScorer`'s
   `ACTIVE`-status/mapping-exists checks are eligibility gates, not urgency-threshold gates). Plan
   should explicitly decide whether `should_pivot` is preserved as a pre-filter (candidate only exists
   when personally resistance-overcome) or dropped in favor of always emitting a scored candidate and
   letting `evaluate_project_switch()` alone decide — not silently inherited from the pre-migration
   code's structure.

## Anti-Drift Hazards

- **Do not use `best_candidate.utility` anywhere in the new materialization branch's `score=`
  argument** — same highest-value regression class as both prior tickets in this epic, now the third
  instance of this exact rule; the raw-score/utility separation is non-negotiable per the ticket's own
  AC.
- **Do not touch `interpret_scar_detection()`** — LEG-RPG-117, a separate method, explicitly out of
  this ticket's scope; its own `"exploration"`/`"investigate"` raw strings already match real enum
  values (see Current Behavior) and need no fix regardless.
- **Do not touch line 179's `current_project_id_set=None` clear inside `interpret_near_death()`** —
  explicitly out of scope per the ticket text ("a clear, not a steal"); confirmed this line lives in
  a different method (`interpret_near_death()`, not `interpret_regional_danger()`).
- **Do not modify `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`, or `_GOAL_UTILITY_SCORE_MAX`
  without an explicit Plan decision recorded** — same constraint ticket 5 already established;
  changing the shared constant/function affects both `ADVENTURE_ROUTE`'s and `SOCIAL_CONTRACT`'s
  already-verified calibration too.
- **Do not silently assume the mechanic becomes live-reachable, or silently assume it stays inert** —
  Risk #1 is a real fork with disclosure obligations either way; picking one implicitly (e.g. by
  accident of implementation convenience) without recording the choice would misrepresent this
  ticket's actual production impact, the same class of omission ticket 5's own investigation was
  careful to avoid for `execute_recruit()`.
- **Do not conflate `should_pivot`'s urgency-vs-resistance check with `evaluate_project_switch()`'s
  retention-margin check** — they are different formulas over different profile fields' derived
  values; collapsing them without an explicit Plan decision risks silently changing which entities
  ever generate a stabilize candidate at all (see Risks #5).
- **Do not widen `test_project_pivot_when_urgency_exceeds_resistance`/`test_no_pivot_when_resistance_high`'s
  assertions beyond what the new architecture actually produces** just to make them pass — the
  ticket's own AC requires "equivalent assertions," not "whatever assertions happen to pass"; if the
  new scorer path cannot reproduce the exact suspend/pivot semantics these tests currently check,
  that is a Plan-level finding to surface, not something to paper over in the test rewrite.
