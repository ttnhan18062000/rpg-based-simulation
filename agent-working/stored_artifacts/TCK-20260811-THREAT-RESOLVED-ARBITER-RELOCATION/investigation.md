---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION
artifact_type: investigation
tags: [cognition, adventure]
---

# Investigation — TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION

## IMPORTANT: line numbers below are freshly re-verified against the current repo state
(post `846d53de` TCK-20260811-ADVENTURE-GOAL-SCORER and post `1fbd2fb4`
TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG). **Every line number in the
ticket body (`intelligence.py:1345`, `:1426`) and in the design doc (`:1341`, `:1422`) is
now stale.** Real current numbers are cited below.

## Current Behavior

### `_threat_resolved()` — `src/domains/adventure/phase.py:27-46`
```python
def _threat_resolved(hero: EntityState, state: AuthoritativeState) -> bool:
    hp_ratio = hero.combat.hp / max(1, hero.combat.max_hp)
    if hp_ratio <= 0.8:
        return False
    nearby_ids = SpatialQueryService.nearby_entities(state, hero.navigation.position, radius=10.0)
    has_hostile = any(
        eid != hero.id
        and (e := state.entities.get(eid)) is not None
        and e.combat.alive
        and e.identity.faction != hero.identity.faction
        for eid in nearby_ids
    )
    return not has_hostile
```
Already has the exact `(hero: EntityState, state: AuthoritativeState) -> bool` signature the
ticket assumes — no signature change needed on relocation, only a module move. Its only
external dependency is `SpatialQueryService.nearby_entities` (`src/engine/spatial_query.py:45-65`),
which itself only needs `state` (via `WorldIndexService.get_indexes(state, dirty)`) — no other
`phase.py`-local state.

**Sole caller today**: `AdventureDecisionPhase.apply()`, `phase.py:151`:
```python
if tick < active_proj.lock_until_tick and not _threat_resolved(hero, state):
    continue
```
`state` is in scope as `apply()`'s first parameter (`phase.py:106`).

**`evaluate_project_switch()` call site inside `apply()`** — `phase.py:192-194`:
```python
strat_upd = StrategicIntelligenceSystem.evaluate_project_switch(
    hero, result.proposed_project, tick
)
```
`state` is in scope here too (same `apply()` call frame).

### `evaluate_project_switch()` — `src/systems/strategic_systems/intelligence.py:930-1011`
Current real signature (**no `state` param today** — confirmed fresh):
```python
@staticmethod
def evaluate_project_switch(
    entity: EntityState,
    candidate_project: ProjectState,
    current_tick: int
) -> Optional[StrategicUpdate]:
```
Locked-branch gate, current exact shape (`intelligence.py:979-999`, re-verified post
`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` which touched only the
`normalized_effective_current_pct` denominator inside this block, not its outer condition):
```python
if current.lock_until_tick > current_tick:
    if candidate_project.kind == "detour":
        pass
    else:
        candidate_max = _score_scale_max(candidate_project.kind)
        current_max = _score_scale_max(current.kind)
        candidate_pct = candidate_project.score / candidate_max
        normalized_effective_current_pct = (current.score / current_max) + (retention_margin / _GOAL_UTILITY_SCORE_MAX)
        if not (candidate_pct > normalized_effective_current_pct
                and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
            return None
```
The **existing design doc** (`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
§5, lines 219-260, already reviewed/resolved) specifies the exact additive shape to use, and it
matches CLAUDE.md's "additive, not a new bypass mechanic" instinct: widen only the **outer** gate
condition, not the inner detour/percentage logic:
```python
if current.lock_until_tick > current_tick and not _threat_resolved(entity, state):
```
i.e. line 979's `if current.lock_until_tick > current_tick:` becomes
`if current.lock_until_tick > current_tick and not _threat_resolved(entity, state):` — everything
inside the block (detour bypass, percentage/urgency-floor check) is untouched. When
`_threat_resolved` is True, the whole locked-branch block is skipped and execution falls straight
to the raw comparison at line 1001 (`if candidate_project.score > effective_current_score:`),
exactly reproducing today's `AdventureDecisionPhase`-only early-release outcome. **Do not** fold
this into the `kind == "detour"` branch as a second unconditional bypass — the design doc
explicitly rejects that shape as reproducing the exact hardcoded-kind-special-case pattern
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` already eliminated once.

### `evaluate_strategic_intent()` — `intelligence.py:1135-` (real production call sites)
Signature: `evaluate_strategic_intent(state: AuthoritativeState, entity: EntityState, force: bool = False, cadence: SystemCadence | None = None) -> StrategicUpdate` (`intelligence.py:1135-1140`). `state` is the first param — in scope everywhere inside.

Two real calls to `evaluate_project_switch` inside this function, both currently
**state-argument-free**, both re-verified at their current (shifted) line numbers:
- `intelligence.py:1346` — `detour_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, detour_proj, current_tick)` (tier-4 detour-suggestion branch)
- `intelligence.py:1456` — `switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick)` (tier-5 goal-scoring branch, now also the landing spot for `AdventureGoalScorer`'s materialized `ADVENTURE_ROUTE` candidates post-ticket-1)

**Correction vs. the ticket body**: the ticket text cites `intelligence.py:1345` and `:1426` (and the
design doc cites `:1341`/`:1422`) — both stale. Real current values are **1346** and **1456**.
The 1345→1346 shift is a single-line drift (likely from `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-
MARGIN-SCALE-BUG`'s comment additions above line 979); the 1426→1456 shift (30 lines) traces to
`TCK-20260811-ADVENTURE-GOAL-SCORER`'s materialization branch (`intelligence.py:1402-1429`,
the `GoalKind.ADVENTURE_ROUTE` handling and its comment block) landing between the two call
sites in tier 5. **The ticket's own "3 real call sites, not 2" count is otherwise correct** —
confirmed by full-repo grep, no 4th production call site exists.

### `SpatialQueryService.nearby_entities()` — `src/engine/spatial_query.py:45-65`
```python
@staticmethod
def nearby_entities(state: AuthoritativeState, pos: tuple[float, float], radius: float, dirty: Optional[Any] = None) -> List[int]:
```
No changes needed — `_threat_resolved()` calls it exactly as today; relocation only changes
which module imports `SpatialQueryService`. **`intelligence.py` does not currently import
`SpatialQueryService`** (confirmed via grep — zero hits in that file today) — relocation must add
`from src.engine.spatial_query import SpatialQueryService` to `intelligence.py`'s import block
(alongside the existing `from src.core.strategic import (...)` block at lines 64-68).
`EntityState`/`AuthoritativeState` are already imported (`intelligence.py:58`), so no new import
needed for those.

## Mechanics / Engine Constraints
- `docs/mechanics/04_strategic_cognition.md` §6.6 (referenced by `_ADVENTURE_ROUTE_SCORE_MAX` at
  `intelligence.py:29-32`) governs the System-A/System-B score-scale split the locked-branch
  percentage check depends on. This ticket's change does not touch that math — it only adds an
  outer short-circuit before it runs — so no mechanics-formula change, only a lock-expiry
  condition widening.
- Architecture Rule (CLAUDE.md): "Decision logic reads state. It does not authoritatively mutate
  durable state." `_threat_resolved()` and the widened lock check are both pure reads (`state`,
  `entity`) — no mutation, consistent with the rule as-is post-relocation.
- Strategic/Tactical Rule (CLAUDE.md): "Do not solve strategic problems by stacking more tactical
  goal scoring." The design doc's resolution (fold into the lock-expiry condition, not a new
  scoring bypass) is directly this rule applied — worth citing explicitly in the plan as the
  rationale for *why* the additive-condition shape was chosen over a second kind-based exemption.

## Docs Requiring Update
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-236 (lines 2696-2715) — both `text` (currently
  says "the lock is bypassed in `AdventureDecisionPhase`", adventure-specific) and `v2_evidence`
  (currently cites `src/domains/adventure/phase.py — _threat_resolved() helper and conditional lock
  check`) must be updated to cite the new `intelligence.py` location and the generalized (not
  adventure-only) scope, per the design doc's own already-resolved §5/§9 decision.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: not owned by
  this ticket to rewrite wholesale (it's a point-in-time design record), but if its own stale line
  citations (`:1341`, `:1422`, `intelligence.py:928-932`) are left uncorrected they will actively
  mislead the next reader the same way this ticket's own body did — flag as a should-fix, not a
  hard AC; leave to Plan's judgment whether to patch just the citations inline.

## Parity Ledger Overlap
- **STRAT-236** (P1, `verified`) — the entry this ticket directly rewrites. Its `test_path`
  (`tests/unit/systems/test_spawn_lock_condition.py::TestLockEarlyRelease::test_lock_released_when_hp_high_and_no_hostiles`)
  still exists and still passes against the relocated function (it exercises `_threat_resolved`
  only indirectly via `AdventureDecisionPhase.apply()`, which keeps working unchanged since
  `phase.py:151`'s own gate is untouched by this ticket — see Anti-Drift Hazards). Not a P0, so a
  passing `test_path` isn't a hard done-checker gate, but it already has one and it should keep
  passing.
- **STRAT-185/STRAT-186/STRAT-187** (all P0, `verified`, `test_path: null` today per the design
  doc's own §9 note) are the entries governing the locked-branch gate this ticket's additive
  condition sits inside. This ticket does not close their `test_path: null` gap (out of scope —
  that's flagged in the design doc as belonging to whichever ticket lands the interruption-
  resistance test suite as their evidence), but the new AC3 regression test is a reasonable
  candidate `test_path` for STRAT-186/187 if Plan wants to close that gap opportunistically; not
  required by this ticket's own acceptance criteria.
- No P0 entry is newly put at risk by this change — the raw/unlocked comparison path (STRAT-185's
  own subject) is explicitly required to stay byte-identical by AC1/AC2.

## Prior Work
- **TCK-20260627-P2A-SPAWN-LOCK-COND** (done) — original `_threat_resolved()` implementation and
  the `AdventureDecisionPhase`-only early-release, plus `tests/unit/systems/test_spawn_lock_condition.py`
  (still the STRAT-236 `test_path`, still adventure-domain-scoped by name/location even after this
  ticket relocates the function it tests).
- **TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION** (done) — replaced the old hardcoded
  `kind == "danger" and score > 80` / `kind == "detour"` allowlist with the generalized
  percentage-based urgency-floor check this ticket's additive condition sits alongside. Directly
  informs why this ticket must not reintroduce a second kind-keyed special case.
  `related_code_areas` empty in `docs/REGISTRY.yaml` for this entry (registry gap, not a real
  absence of overlap — code area is unambiguously `intelligence.py`'s locked-branch gate).
- **TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG** (done, lands immediately before
  this ticket in the working log) — most recent modification to the exact block this ticket
  extends (`intelligence.py:979-999`). Changed only the `retention_margin` normalization
  denominator; the outer `if current.lock_until_tick > current_tick:` line this ticket must widen
  is untouched by that commit. Also the source of `test_score_normalization.py`'s growth from
  4 to 6 `evaluate_project_switch()` calls (see Assumptions/Open Questions — this, not
  `TCK-20260811-ADVENTURE-GOAL-SCORER`, is why the "25" count in the ticket's own Assumptions
  section is now stale).
- **TCK-20260811-ADVENTURE-GOAL-SCORER** (done, epic ticket 1/10, this epic) — added the
  `GoalKind.ADVENTURE_ROUTE` materialization branch at `intelligence.py:1402-1429`, which is what
  pushed the second `evaluate_project_switch` call site from `:1426` to `:1456`. Did not touch
  `test_score_normalization.py` (confirmed via `git show --stat`) or the locked-branch gate.

## Risks and Open Questions

### OPEN DESIGN DECISION — require vs. default `state` param (ticket's own flagged question)
**Re-verified real current count: 27 direct `evaluate_project_switch(...)` test call sites with no
`state` argument across the 5 named files** (not 25 — see below), confirmed by direct grep + manual
line-by-line read of each file, excluding docstring/comment/method-name mentions that are not
actual calls:
- `tests/unit/strategic/test_score_normalization.py`: 6 (lines 52, 73, 110, 140, 173, 181)
- `tests/unit/strategic/test_interruption_resistance.py`: 13 (lines 49, 62, 74, 92, 100, 118, 124, 169, 186, 203, 230, 249, 268)
- `tests/unit/strategic/test_project_continuity.py`: 5 (lines 47, 55, 76, 83, 88)
- `tests/unit/strategic/test_strategic_reprioritization.py`: 1 (line 46)
- `tests/unit/systems/test_quest_activation_pathway.py`: 2 (lines 228, 283)
- **Total: 27**, not 25.

**Root cause of the drift, confirmed via `git show --stat`**: contrary to what this prompt's own
framing suggested, `TCK-20260811-ADVENTURE-GOAL-SCORER` (epic ticket 1) did **not** touch
`test_score_normalization.py` at all. The +2 came from `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-
MARGIN-SCALE-BUG` (a *different*, also-just-landed ticket — listed in this ticket's own Related
Tickets), which renamed one existing test and added one brand-new test
(`test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`,
`test_score_normalization.py:114-181`), each containing one `evaluate_project_switch()` call. Both
of the epic's own child-ticket-1 changes and this sibling ticket's changes landed the same day; the
"25" estimate predates both.

**Concrete recommendation: (b) — `state: Optional[AuthoritativeState] = None`, skip the
`_threat_resolved` check when `state is None`.** Reasoning, evidence-based rather than a coin flip:
- **Option (a) would silently break correctness in a large subset of the 27 existing tests, not
  just require boilerplate.** `V2EntityBuilder`'s default `CombatComponent` is `hp=100, max_hp=100`
  (`src/core/state.py:299-300`, `src/core/builder.py:97`) — i.e. `hp_ratio == 1.0 > 0.8` — and none
  of the 27 existing call sites construct any other entity or populate `state.entities` with a
  hostile. If forced to pass *some* minimal `AuthoritativeState` (e.g. an empty one, as
  `test_spawn_lock_condition.py`'s own ~25-field `_make_state()` helper would produce), `_threat_
  resolved()` would evaluate **True** (full HP, zero hostiles found) for every one of those tests
  by construction, not by test intent. Since many of the 27 (e.g. `test_project_lock_prevents_
  switching`-style scenarios in `test_interruption_resistance.py`/`test_project_continuity.py`) are
  specifically asserting that a locked project is **retained** (`result is None`) under the
  percentage-based gate, a threat-resolved-by-default entity would make the outer condition false,
  skip the entire locked-branch gate, fall to the raw comparison, and flip several of these tests'
  expected outcomes — a correctness regression masquerading as "just adding a required param."
  Avoiding this would require every one of the 27 call sites to *also* reason about HP/hostile
  placement (an orthogonal concern to what each test is actually validating), which is real,
  non-mechanical design work, not a one-line fixture threading exercise.
- **Option (b) has zero blast radius on the 27 sites** and satisfies AC1's explicit "no behavior
  change on the raw/unlocked comparison path" requirement by construction — untouched tests stay
  byte-identical, no fixture changes needed.
- **Matches an existing repo convention**: `AdventureDecisionPhase.apply()` itself already uses
  `Optional[X] = None` for context-dependent side inputs it doesn't always have
  (`trace_writer`, `faction_directives`, `factions` — `phase.py:107-110`), and
  `evaluate_strategic_intent()` does the same for `cadence` (`intelligence.py:1139`). Defaulting
  `state` to `None` for a check that legitimately doesn't apply when no world context is supplied
  is consistent with that pattern, not a new idiom.
- **Real production call sites carry no risk either way**: all 3 (`intelligence.py:1346`, `:1456`,
  `phase.py:192`) already have `state` in scope and will always pass it explicitly per AC1 — the
  `None` default only ever gets exercised by test code that doesn't care about threat-resolution
  semantics.
- The only thing Option (b) requires discipline on: AC3's new regression test **must** explicitly
  construct and pass a real `state`, or it would trivially vacuously pass by never exercising the
  new branch at all (see Test Plan).

This is a recommendation for Plan to adopt or override — Plan should still record the decision
explicitly per the ticket's own "must be resolved explicitly at Plan time, not silently picked"
requirement; this investigation is not the authorizing decision.

### `test_phase3_project_switch_routing_guard.py` — confirmed no update needed
Read in full (`tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py:19-61`).
Its AST walk matches on `ast.Call` nodes where `func.attr == "evaluate_project_switch"` (or
`func.id`) — it does **not** inspect the call's arguments/arity at all, only the callee name. Adding
a `state=state` keyword argument (or a positional `state` arg) to the `phase.py:192` call site does
not change the AST node's `func.attr`, so both assertions
(`test_apply_commit_branch_does_not_construct_strategic_update_directly` and
`test_apply_module_imports_strategic_intelligence_system`) continue to pass unmodified. No change
required to this test file.

### `phase.py:151`'s pre-existing redundant evaluation (ticket's own disclosed non-issue)
Confirmed: `phase.py:151`'s own gate (`if tick < active_proj.lock_until_tick and not
_threat_resolved(hero, state): continue`) and the new check inside `evaluate_project_switch()` will
both evaluate `_threat_resolved()` on the same tick for the same entity when routing proceeds past
`phase.py:151`. This is real (confirmed by tracing both call paths) but the ticket explicitly
disclosed and pre-authorized it as harmless/out-of-scope-to-optimize — not re-litigated here.

## Anti-Drift Hazards
- **Do not turn the additive check into a second unconditional bypass keyed to `kind`.** The design
  doc explicitly rejects this shape (§5, "the wrong shape... reproduce the exact hardcoded,
  kind-string-special-case pattern"). The correct shape widens the *outer* `if current.lock_until_
  tick > current_tick:` condition only — implementation must not touch the `kind == "detour"` /
  percentage-check logic inside the block at all.
- **Do not touch `phase.py:151`'s existing gate.** It's a separate, still-correct, still-necessary
  check (it governs whether `AdventureDecisionPhase` even attempts routing for a hero at all,
  before candidates are generated) — this ticket's job is `evaluate_project_switch()`'s *own*
  internal gate, which is a different, independent enforcement point for the same rule (defense in
  depth against any future second caller of `evaluate_project_switch()` that doesn't have its own
  `phase.py:151`-style pre-filter).
- **Do not silently pick the require-vs-default `state` design without recording the decision** —
  the ticket explicitly calls this out as something that must not be silently defaulted.
- **`_score_scale_max()` classification (`intelligence.py:89-`) is by enum *class* identity, not
  string value** (`ProjectKind.HARVESTING` and `GoalKind.HARVESTING` share the string `"harvesting"`
  but are different classes) — irrelevant to this ticket's own change (which sits outside that
  block), but any new regression test constructing a `ProjectState(kind=GoalKind.COMBAT_RETREAT,
  ...)` for AC3 must use the actual `GoalKind.COMBAT_RETREAT`/`GoalKind.RECOVER` enum members
  (`src/core/strategic.py:129-130`), not the string `"combat_retreat"`, or `_score_scale_max` would
  misclassify it — though note the locked-branch percentage check is never reached in AC3's
  scenario once `_threat_resolved` short-circuits the outer condition, so this only matters if the
  new test also wants to exercise the pre-existing percentage path as a contrast case.
- **`STRAT-236`'s `test_path` stays pointed at `test_spawn_lock_condition.py`** — that test exercises
  the behavior through `AdventureDecisionPhase.apply()`, which still works unchanged (its own
  `phase.py:151` gate is untouched). Do not feel obligated to move or duplicate those tests into
  `tests/unit/strategic/` — AC3's new test is additive coverage for the *generalized* (non-adventure)
  path, not a replacement for the existing adventure-path coverage.
- **`GoalKind` vs `ProjectKind` vocabulary split is explicitly out of scope** (per `_score_scale_max`'s
  own docstring, "tracked under D22/C4") — do not attempt to unify them while touching this area.
