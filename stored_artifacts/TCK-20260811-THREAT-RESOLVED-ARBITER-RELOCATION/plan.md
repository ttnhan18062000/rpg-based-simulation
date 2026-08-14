---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION
artifact_type: plan
tags: [cognition, adventure]
---

# Implementation Plan — TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION

## Summary

Relocate the pure-read helper `_threat_resolved()` from `src/domains/adventure/phase.py` into
`src/systems/strategic_systems/intelligence.py` as a module-level function co-located with
`evaluate_project_switch()`, and widen `evaluate_project_switch()`'s own locked-branch gate to also
skip when the triggering threat has resolved. Per investigation.md's evidence-based recommendation,
the ticket's flagged open design decision is resolved here as: `evaluate_project_switch()` gains
`state: Optional[AuthoritativeState] = None` — a **default**, not a required parameter — with the
new check only evaluated when `state is not None`. This is not a stylistic choice; it is required
for correctness. `V2EntityBuilder`'s default `CombatComponent` is `hp=100/max_hp=100`
(`src/core/state.py:299-300` field defaults via `src/core/builder.py:97`), so any of the 27 existing
direct `evaluate_project_switch()` test call sites that omitted `state` would, if `state` were
required and backfilled with a minimal empty `AuthoritativeState`, evaluate `_threat_resolved()` as
`True` by construction (full HP, zero hostiles found in an empty `state.entities`) — silently
flipping several existing lock-retention (`result is None`) assertions into lock-release assertions.
The default-`None`, skip-when-`None` design has zero blast radius on those 27 sites and satisfies
AC1's "no behavior change on the raw/unlocked comparison path" requirement by construction. The
widened condition itself follows the design doc's already-reviewed §5 shape: the outer
`if current.lock_until_tick > current_tick:` gate itself is unchanged, and the new `threat_resolved`
check is computed lazily as the first statement *inside* that gate (not above or outside it), with
the existing `kind == "detour"` / percentage / urgency-floor logic nested one level deeper under a
new `if not threat_resolved:` — untouched in content, only in nesting depth. Computing
`threat_resolved` inside the lock-active gate (rather than unconditionally before it) matters
because `_threat_resolved()` calls `SpatialQueryService.nearby_entities()`, an O(radius^2)
tile-grid scan; all 3 real production call sites always pass a real `state`, so an eager,
outside-the-gate computation would run that scan on every `evaluate_project_switch()` call for any
unlocked, healthy entity too — not just the locked case this ticket targets. This avoids both the
kind-keyed-special-case anti-pattern `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` already
eliminated once, and an undisclosed new compute cost on the common unlocked path.

## Steps

### Step 1 — Relocate `_threat_resolved()` into `intelligence.py`; update `phase.py`'s import
**Files:** `src/systems/strategic_systems/intelligence.py`, `src/domains/adventure/phase.py`

**Change:**
- In `intelligence.py`: add `from src.engine.spatial_query import SpatialQueryService` to the
  import block, placed immediately after the `from src.core.strategic import (...)` block
  (`intelligence.py:64-68`). Confirmed by direct read that `intelligence.py` currently has zero
  references to `SpatialQueryService` (no existing import to collide with) and that `EntityState`/
  `AuthoritativeState` are already imported at `intelligence.py:58`
  (`from src.core.state import EntityState, AuthoritativeState`) — no new import needed for those.
- In `intelligence.py`: insert a new module-level function immediately after `_score_scale_max()`
  ends and before `class StrategicIntelligenceSystem:` begins (confirmed exact insertion point:
  `_score_scale_max()` ends at `intelligence.py:108`, `class StrategicIntelligenceSystem:` starts at
  `intelligence.py:111` — insert in the blank space between them), matching `_score_scale_max()`'s
  own placement pattern as a bare module-level helper called without a class prefix inside
  `evaluate_project_switch()`. Body is a verbatim copy of the current `phase.py:27-46` function, no
  signature change (confirmed identical read this session):
  ```python
  def _threat_resolved(hero: EntityState, state: AuthoritativeState) -> bool:
      """
      Return True when the triggering threat for a survival lock is no longer active:
      entity HP has recovered above 80% AND no hostile entity is within interaction radius.

      Used as an early-release condition inside evaluate_project_switch()'s locked-branch gate
      so that entities are not held idle in a project lock after the threat passes. Relocated
      from src/domains/adventure/phase.py (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION) to
      generalize beyond AdventureDecisionPhase's original sole-caller scope. STRAT-236.
      """
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
- In `phase.py`: delete the function body at `phase.py:27-46` (the old `_threat_resolved`
  definition) entirely.
- In `phase.py`: remove the now-dead import at `phase.py:21`
  (`from src.engine.spatial_query import SpatialQueryService`). Confirmed by grep this session that
  `SpatialQueryService` has exactly two references in `phase.py` today — the import at line 21 and
  the one call inside `_threat_resolved()` at line 38 — so once the function moves, this import has
  zero remaining uses in the file and must not be left dangling.
- In `phase.py`: add a new import to pull the relocated symbol back in:
  `from src.systems.strategic_systems.intelligence import _threat_resolved`, placed in the existing
  import block (e.g. adjacent to the existing `from src.systems.strategic import
  StrategicIntelligenceSystem` at `phase.py:20`). This must import from
  `src.systems.strategic_systems.intelligence` directly, **not** from the `src.systems.strategic`
  compatibility wrapper (`src/systems/strategic.py:1-10`) — confirmed by reading that wrapper file
  this session that its `__all__` exports only `["StrategicIntelligenceSystem"]`; `_threat_resolved`
  is not re-exported through it.
- **Other writer / caller enumeration for `_threat_resolved`:** confirmed by repo-wide grep this
  session, the only two call sites of `_threat_resolved` anywhere in `src/` are `phase.py:151`
  (unchanged by this step — same call expression, now resolving to the imported symbol instead of a
  local module-level def) and the new call this ticket adds inside `evaluate_project_switch()`
  (Step 2). No other module calls it. `tests/integration/domains/adventure/
  test_phase3_adventure_decision_phase.py:91` references `_threat_resolved()` only in a **docstring
  comment**, not a live import or call — confirmed by grep; no source change needed there, listed
  here only so Implement does not mistake it for a call site requiring an import fix.
- **Import-cycle check performed this session:** `phase.py` importing from
  `src.systems.strategic_systems.intelligence` introduces no new cycle — `intelligence.py` already
  imports `from src.domains.adventure.mapper import RouteToProjectMapper` (`intelligence.py:79`),
  and `mapper.py`'s own imports (confirmed by direct read) are limited to
  `src.core.strategic` and `src.domains.adventure.schema` — it does not import `phase.py`. `phase.py`
  already transitively depends on `intelligence.py` today via the `src.systems.strategic` wrapper
  (`phase.py:20`), so this adds a second import of an already-depended-on module, not a new
  dependency edge.

**Do NOT touch:** `phase.py:151`'s conditional logic itself (`if tick < active_proj.lock_until_tick
and not _threat_resolved(hero, state): continue`) — only the symbol resolution mechanism changes
(local def → import), the call expression and behavior are identical. Do NOT touch
`_resolve_cognition_profile_id` (`phase.py:49-80`) or `_supports_adventure_routing`
(`phase.py:83-96`) — both are `DELETE-ADVENTURE-DECISION-PHASE`'s (C3) job per the ticket's Out of
Scope. Do NOT touch any other part of `AdventureDecisionPhase`'s class body (`phase.py:99-`) beyond
the one call-site edit needed in Step 3.

**Verify:** `tests/unit/systems/test_spawn_lock_condition.py` (all 4 test classes) must still pass
unmodified — it exercises `_threat_resolved` indirectly via `AdventureDecisionPhase.apply()`
(`phase.py:151`'s gate), which is functionally identical after this step. A clean `python -c "import
src.domains.adventure.phase"` and `python -c "import src.systems.strategic_systems.intelligence"`
(no `ImportError`/circular-import failure) confirms the import restructuring is sound before running
the full suite.

---

### Step 2 — Widen `evaluate_project_switch()`'s signature and lock-expiry condition
**Files:** `src/systems/strategic_systems/intelligence.py`

**Change:**
- Current signature (`intelligence.py:930-934`, confirmed by direct read this session — matches
  investigation.md exactly, no `state` param today):
  ```python
  @staticmethod
  def evaluate_project_switch(
      entity: EntityState,
      candidate_project: ProjectState,
      current_tick: int
  ) -> Optional[StrategicUpdate]:
  ```
  New signature — add `state` as a 4th parameter with a `None` default (per this plan's Summary
  decision):
  ```python
  @staticmethod
  def evaluate_project_switch(
      entity: EntityState,
      candidate_project: ProjectState,
      current_tick: int,
      state: Optional[AuthoritativeState] = None
  ) -> Optional[StrategicUpdate]:
  ```
  `Optional` is already imported (`intelligence.py:17`,
  `from typing import Dict, List, Optional, Any, TYPE_CHECKING`); `AuthoritativeState` is already
  imported (`intelligence.py:58`). No new imports needed for this step (Step 1 already added the
  `SpatialQueryService` import that `_threat_resolved` itself needs).
- Current locked-branch gate (`intelligence.py:974-999`, confirmed by direct read this session,
  re-verified as untouched by the most recent prior edit to this block —
  `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`, which only changed the
  `normalized_effective_current_pct` denominator inside the `else` branch, not the outer `if` or the
  lines above it):
  ```python
          # Logic ID: STRAT-005 (Project switching uses interruption resistance)
          retention_margin = profile.interruption_resistance * profile.resistance_multiplier
          # Logic ID: STRAT-006 (Current project gets retention priority)
          effective_current_score = current.score + retention_margin

          if current.lock_until_tick > current_tick:
              ...
  ```
  New shape — keep the outer `if current.lock_until_tick > current_tick:` gate exactly as it is
  today, and compute `threat_resolved` **lazily, inside** that gate, as its own first statement,
  with a second nested `if not threat_resolved:` wrapping the existing detour/percentage/
  urgency-floor logic. **Do not** compute `threat_resolved` (or call `_threat_resolved` at all)
  above/outside the outer `if current.lock_until_tick > current_tick:` line, and do not write
  `not _threat_resolved(entity, state)` directly inline in that outer condition either — both of
  those shapes evaluate `state is not None and _threat_resolved(entity, state)` unconditionally on
  every call, including every call where the current project is not even locked (the common case:
  all 3 real production call sites always pass a real `state`, so an unlocked-but-healthy entity
  would trigger the spatial scan on every single `evaluate_project_switch()` invocation for it).
  `_threat_resolved` calls `SpatialQueryService.nearby_entities()`, an O(radius²) tile-grid scan
  (~441 tile lookups at the hardcoded `radius=10.0`) — this file already carries PERF-* Logic IDs
  and an explicit STRAT-PERF-001 "consolidated O(N) pass" optimization, so paying that cost on the
  unlocked path is new, undisclosed compute cost this ticket must not introduce. Computing
  `threat_resolved` **inside** the `current.lock_until_tick > current_tick:` gate means the spatial
  query only ever runs when the current project is actually locked — the only case the check is
  meant to affect — and `evaluate_project_switch()` retains its existing zero-cost behavior for
  every unlocked call, byte-identical to today. (`state is None` still short-circuits `and` before
  `_threat_resolved` is ever called either way — that half of the null-safety guarantee is
  unchanged.) The lazy, nested form:
  ```python
          # Logic ID: STRAT-005 (Project switching uses interruption resistance)
          retention_margin = profile.interruption_resistance * profile.resistance_multiplier
          # Logic ID: STRAT-006 (Current project gets retention priority)
          effective_current_score = current.score + retention_margin

          if current.lock_until_tick > current_tick:
              # STRAT-236 (generalized): when a real world `state` is supplied and the triggering
              # threat has resolved (HP > 80%, no hostile within radius 10.0), the lock is treated
              # as already expired. `state is None` (the default for the 27 pre-existing direct
              # test call sites that predate this check) short-circuits `and` before
              # `_threat_resolved` is ever called, preserving today's behavior exactly. Computed
              # here, inside the lock-active gate, rather than above it, so the O(radius^2) spatial
              # scan in SpatialQueryService.nearby_entities() only runs when the current project is
              # actually locked — not on every evaluate_project_switch() call for an unlocked,
              # healthy entity (the common case across all 3 real production call sites).
              threat_resolved = state is not None and _threat_resolved(entity, state)

              if not threat_resolved:
                  ...
  ```
  Everything inside the inner `if not threat_resolved:` block (the `kind == "detour"` bypass and
  the `candidate_pct`/`normalized_effective_current_pct`/urgency-floor comparison,
  `intelligence.py:986-999`) is **byte-identical, untouched** — it is now nested one level deeper
  under `if not threat_resolved:`, but no statement inside it changes. When `threat_resolved` is
  `True`, the inner block is skipped and execution falls straight to the raw comparison at
  `intelligence.py:1001` (`if candidate_project.score > effective_current_score:`), exactly
  reproducing today's `AdventureDecisionPhase`-only early-release outcome for the case where
  `state` is supplied. When `current.lock_until_tick <= current_tick` (the unlocked path), the
  outer `if` is never entered at all, `threat_resolved` is never computed, and
  `_threat_resolved`/`SpatialQueryService.nearby_entities()` are never called — identical to
  today's behavior and cost on that path.
- **Other writers to this exact block (`intelligence.py:974-999`):** repo-wide, this block has one
  prior modification in the current working log —
  `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` (already landed, not concurrent with
  this session) — which touched only the `normalized_effective_current_pct` line inside the `else`
  branch. No other in-flight ticket touches this block per `tickets/inprogress/` at investigation
  time. The three call sites that invoke this function (Step 3) are the only "writers" of the
  `state` argument this step consumes; none of them write to the function body itself.

**Do NOT touch:** the `kind == "detour"` branch or the percentage/urgency-floor `else` branch
(`intelligence.py:986-999`) — do not fold the new check into either as a second special case. Do NOT
touch the raw comparison at `intelligence.py:1001` or the no-current-project / stale-current
early-return branches at `intelligence.py:959-972`. Do NOT touch `_score_scale_max()`
(`intelligence.py:90-108`) or the `_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX`/
`_INTERRUPTION_URGENCY_FLOOR_PCT` module constants (`intelligence.py:29-53`).

**Verify:** `test_evaluate_project_switch_signature_accepts_state_kwarg` and
`test_evaluate_project_switch_unlocked_path_identical_with_and_without_state` (Step 4) and
`test_evaluate_project_switch_locked_project_released_when_threat_resolved` (Step 5) — plus the full
existing 27-call-site regression surface across `test_score_normalization.py`,
`test_interruption_resistance.py`, `test_project_continuity.py`, `test_strategic_reprioritization.py`,
`test_quest_activation_pathway.py` staying green with zero edits.

---

### Step 3 — Thread `state=state` through the 3 real production call sites
**Files:** `src/domains/adventure/phase.py`, `src/systems/strategic_systems/intelligence.py`

**Change:**
- `phase.py:192-194` (inside `AdventureDecisionPhase.apply()`, confirmed `state` is in scope as
  `apply()`'s first parameter at `phase.py:106`):
  ```python
  strat_upd = StrategicIntelligenceSystem.evaluate_project_switch(
      hero, result.proposed_project, tick, state=state
  )
  ```
- `intelligence.py:1346` (inside `evaluate_strategic_intent()`'s tier-4 detour-suggestion branch,
  confirmed `state` is in scope as `evaluate_strategic_intent()`'s first parameter at
  `intelligence.py:1136`):
  ```python
  detour_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, detour_proj, current_tick, state=state)
  ```
- `intelligence.py:1456` (inside `evaluate_strategic_intent()`'s tier-5 goal-scoring branch, same
  enclosing function, same `state` in scope):
  ```python
  switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick, state=state)
  ```
- **Other callers of `evaluate_project_switch` enumerated:** repo-wide grep confirms exactly 3
  production call sites (matching the ticket's own "3 real call sites, not 2" claim, re-confirmed
  fresh this session) and 27 direct test call sites across 5 test files (enumerated in
  investigation.md's Risks section) that are deliberately **not** edited by this step — they rely on
  Step 2's `None` default to keep passing unmodified. No other production module calls
  `evaluate_project_switch`.

**Do NOT touch:** any of the 27 existing direct test call sites in `test_score_normalization.py`,
`test_interruption_resistance.py`, `test_project_continuity.py`, `test_strategic_reprioritization.py`,
`test_quest_activation_pathway.py` — they must remain byte-identical per AC1 and the Summary's
design decision. Do NOT add a `state=` argument to any of them as part of this step (new tests that
*need* a real `state` are added separately in Steps 5 and 6, in new/different test functions, not by
editing these 27 existing calls). Do NOT touch `phase.py:151`'s own gate (already covered by Step
1's guard).

**Verify:** `test_three_production_call_sites_thread_state_argument` (Step 4, new AST guard file) —
fails loudly if any of these 3 sites regresses or a 4th site is added without threading `state`.
`test_apply_commit_branch_does_not_construct_strategic_update_directly` and
`test_apply_module_imports_strategic_intelligence_system`
(`tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`) — confirmed this
session by full read that this file's AST walk matches on `ast.Call` nodes where `func.attr ==
"evaluate_project_switch"` only (no argument/arity inspection), so adding `state=state` to the
`phase.py:192` call does not require any change to this file and both its assertions continue to
pass unmodified.

---

### Step 4 — AC1 test coverage: signature, unlocked-path parity, call-site threading guard
**Files:** `tests/unit/strategic/test_interruption_resistance.py` (2 new tests),
new file `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py` (1 new test)

**Change:**
- Add `test_evaluate_project_switch_signature_accepts_state_kwarg` to
  `test_interruption_resistance.py`, reusing that file's existing `_make_entity()` helper
  (`test_interruption_resistance.py:19-35`, confirmed present this session — builds a minimal
  `EntityState` via `V2EntityBuilder(1).kind("hero").location(5.0, 5.0).strategic(projects=...,
  current_project_id=...)`). Assert both of the following succeed without raising: (a) calling
  `evaluate_project_switch(entity, candidate, current_tick, state=state)` with a real
  `AuthoritativeState` built via a local minimal-fixture pattern (following
  `tests/unit/systems/test_spawn_lock_condition.py:39-64`'s `_make_state()` shape — all
  `AuthoritativeState` fields are required positionally/by-keyword per its dataclass definition, so
  a full field list is needed, not a partial one), and (b) calling it with no `state` argument at
  all (backward-compat smoke test for the 27 untouched call sites' calling convention).
- Add `test_evaluate_project_switch_unlocked_path_identical_with_and_without_state` to the same
  file. Construct an *unlocked* current project (`current.lock_until_tick <= current_tick`, e.g.
  `lock_until_tick=0` against `current_tick=10`, mirroring existing unlocked-path tests already in
  this file). Call `evaluate_project_switch` twice with identical `entity`/`candidate`/`current_tick`
  — once with `state=<a real AuthoritativeState>`, once with no `state` argument — and assert the
  two results compare equal (both `None`, or both `StrategicUpdate`s with identical
  `current_project_id_set`/`current_objective_id_set`/score-derived fields). This proves `state`
  cannot leak into the unlocked raw-comparison path at `intelligence.py:1001`, which Step 2's change
  must not touch.
- New file `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py`, following
  the exact AST-walk pattern already used in
  `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` (confirmed read this
  session). Add `test_three_production_call_sites_thread_state_argument`: use
  `inspect.getsource(AdventureDecisionPhase.apply)` and
  `inspect.getsource(StrategicIntelligenceSystem.evaluate_strategic_intent)`, `ast.parse` +
  `ast.walk` each, and for every `ast.Call` node whose callee (`func.attr` for `ast.Attribute` or
  `func.id` for `ast.Name`) equals `"evaluate_project_switch"`, assert the call carries a `state`
  argument — either a 4th positional arg or a `state=` keyword (check `len(node.args) >= 4` or
  `any(kw.arg == "state" for kw in node.keywords)`). Assert exactly 3 such `Call` nodes are found
  total across the two source strings combined (1 in `apply()`, 2 in `evaluate_strategic_intent()`),
  guarding against both a missed site and a silently-added 4th site.

**Do NOT touch:** any of the 27 pre-existing call sites (see Step 3's guard) — these new tests are
additive, not replacements. Do NOT modify `test_phase3_project_switch_routing_guard.py` itself (no
change required, confirmed by investigation).

**Verify:** the 3 new tests themselves, run via
`pytest tests/unit/strategic/test_interruption_resistance.py
tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py -v`.

---

### Step 5 — AC2 test coverage: locked + HP>80% + no hostile → treated as expired, falls to raw comparison
**Files:** `tests/unit/strategic/test_interruption_resistance.py` (1 new test)

**Change:** Add `test_evaluate_project_switch_locked_project_released_when_threat_resolved`. Build
an entity with a locked current project (`lock_until_tick > current_tick`) via the file's existing
`_make_entity()` helper pattern, with `entity.combat.hp/max_hp > 0.8` (reuse
`V2EntityBuilder(1).replace_combat(CombatComponent(hp=100, max_hp=100, ...))` — the same
`CombatComponent` construction already used in `test_spawn_lock_condition.py:66-70`). Build a
minimal `AuthoritativeState` (per Step 4's `_make_state()` guidance) whose `entities` dict contains
only this one entity — no hostile — so `_threat_resolved` returns `True` via the empty-`nearby_ids`
path. Construct a `candidate_project` scored to **fail** the old percentage/urgency-floor gate
(`candidate_pct <= normalized_effective_current_pct` or `candidate_pct <= 0.8`) but **pass** the raw
comparison (`candidate_project.score > effective_current_score`) — this combination proves the
short-circuit is real and not accidentally equivalent to the pre-existing gate (a candidate that
would also pass the old gate would not distinguish the two code paths). Call
`evaluate_project_switch(entity, candidate, current_tick, state=state)` and assert the result is a
non-`None` `StrategicUpdate` with `current_project_id_set == candidate.id`.

Also required as a **regression confirmation, not a new test**: explicitly re-run
`tests/unit/systems/test_spawn_lock_condition.py::TestLockEarlyRelease::test_lock_released_when_hp_high_and_no_hostiles`
post-Step-1/2/3 and confirm it still passes unmodified — this is the "byte-identical to today's
AdventureDecisionPhase-only behavior" half of AC2 (already-existing coverage via `phase.py:151`'s
untouched gate, not new coverage to add).

**Do NOT touch:** `test_spawn_lock_condition.py` itself — do not weaken, rewrite, or duplicate its
assertions to "make the relocation pass"; it must pass as-is.

**Verify:** the new test plus the named regression-confirmation test, both green.

---

### Step 6 — AC3 test coverage: COMBAT_RETREAT/RECOVER project locked via a non-adventure (System B) caller, threat resolved → early-released
**Files:** new file `tests/unit/strategic/test_threat_resolved_lock_release.py`

**Change:** Create this new dedicated file (distinct from `test_spawn_lock_condition.py`, which
stays adventure-domain-scoped and unmodified per Anti-Drift Hazards). Include a local `_make_state()`
helper following `test_spawn_lock_condition.py:39-64`'s full-field-list shape (all
`AuthoritativeState` dataclass fields), and a local entity-builder helper following
`test_interruption_resistance.py`'s `_make_entity()` / `test_spawn_lock_condition.py`'s
`_make_locked_hero()` patterns.

- `test_combat_retreat_project_locked_via_system_b_early_released_when_threat_resolved`: construct
  an entity whose current project is `ProjectState(id=..., kind=GoalKind.COMBAT_RETREAT,
  status=ProjectStatus.ACTIVE, lock_until_tick=<current_tick + N>, score=..., objectives=[...],
  active_objective_id=...)` — **use the actual `GoalKind.COMBAT_RETREAT` enum member**
  (`src/core/strategic.py:129`, confirmed this session), not the string `"combat_retreat"`, per
  `_score_scale_max()`'s class-identity classification (`intelligence.py:90-108`: `isinstance(kind,
  ProjectKind)` vs. everything else, including `GoalKind`, falling to `_GOAL_UTILITY_SCORE_MAX`).
  Set the current project on `entity.strategic` directly (mirroring
  `test_spawn_lock_condition.py:98-105`'s `fast_replace(entity, strategic=new_strat)` pattern) — do
  **not** route through `AdventureDecisionPhase` at all; the point of this test is that the caller
  is not the adventure domain. Set `entity.combat.hp/max_hp > 0.8`. Build `state` whose `entities`
  contains only this entity (no hostile). Construct a `candidate` scored to clearly win the raw
  comparison (`candidate.score > effective_current_score`). Call
  `StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick,
  state=state)` directly. Assert the result is a `StrategicUpdate` with
  `current_project_id_set == candidate.id` (genuinely released, not just "not blocked") — i.e. same
  shape of assertion as Step 5's test, but with a `GoalKind`-typed current project and no
  `AdventureDecisionPhase` involvement, proving the generalized (non-adventure) path this ticket's
  AC3 requires.
- `test_combat_retreat_project_locked_via_system_b_retained_when_threat_still_active`: same setup,
  but either `hp/max_hp <= 0.8` or a hostile entity (opposing `identity.faction`, `combat.alive =
  True`) placed within radius 10.0 of the hero's position in `state.entities` (reuse
  `test_spawn_lock_condition.py:109-114`'s `_make_hostile()` pattern). Use a `candidate` that would
  fail the pre-existing percentage/urgency-floor gate. Assert the result is `None` — the lock is
  still enforced, proving the new check is genuinely conditional and not an unconditional bypass
  (e.g. guards against a stray `not False` / misplaced `or True` implementation error in Step 2).

**Do NOT touch:** `tests/unit/systems/test_spawn_lock_condition.py` — it is not renamed, moved, or
duplicated; it remains STRAT-236's `test_path` for the adventure-domain-specific coverage. Do NOT
attempt to unify `GoalKind`/`ProjectKind` vocabulary while writing this test (out of scope, tracked
under D22/C4 per `_score_scale_max()`'s own docstring).

**Verify:** both new tests in this file, run via
`pytest tests/unit/strategic/test_threat_resolved_lock_release.py -v`.

---

### Step 7 — Update STRAT-236's `text` and `v2_evidence` in the parity ledger
**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** STRAT-236's entry is at `strategic_cognition.yaml:2696-2715` (confirmed by direct read
this session). Current content:
```yaml
- id: STRAT-236
  text: >-
    Project lock (lock_until_tick) has a conditional early-release path: when HP ratio
    > 0.8 AND no alive hostile entity of a different faction is within radius 10.0,
    the lock is bypassed in AdventureDecisionPhase even before lock_until_tick expires.
    This prevents cascading 10-tick relocks from creating >50-tick dead windows after
    combat (D06 F2 — 200-tick activation delay). All lock assignments are capped at
    current_tick + 50 ticks maximum.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >-
    src/domains/adventure/phase.py — _threat_resolved() helper and conditional lock check
    (TCK-20260627-P2A-SPAWN-LOCK-COND). src/domains/adventure/mapper.py:L101,
    src/systems/strategic_systems/intelligence.py:L1266,L1340 — cap via min(N, tick+50).
  proof_type: parity
  test_path: >-
    tests/unit/systems/test_spawn_lock_condition.py::TestLockEarlyRelease::test_lock_released_when_hp_high_and_no_hostiles
  divergence_note: null
  support_boundary: null
```
Update both `text` and `v2_evidence` (both fields, per AC4, not just `v2_evidence`). New content:
```yaml
  text: >-
    Project lock (lock_until_tick) has a conditional early-release path: when HP ratio
    > 0.8 AND no alive hostile entity of a different faction is within radius 10.0,
    the lock is treated as expired inside evaluate_project_switch()'s own locked-branch
    gate — generalized (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION) beyond the
    original AdventureDecisionPhase-only scope to any caller that supplies a real
    AuthoritativeState. This prevents cascading 10-tick relocks from creating >50-tick
    dead windows after combat (D06 F2 — 200-tick activation delay). All lock assignments
    are capped at current_tick + 50 ticks maximum.
  v2_evidence: >-
    src/systems/strategic_systems/intelligence.py — _threat_resolved() helper (relocated
    from src/domains/adventure/phase.py, TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION;
    originally TCK-20260627-P2A-SPAWN-LOCK-COND) and the widened lock-expiry condition
    inside evaluate_project_switch()'s locked-branch gate. AdventureDecisionPhase's own
    pre-filter at src/domains/adventure/phase.py:151 remains a separate, still-active gate.
    Cap via min(N, tick+50): src/domains/adventure/mapper.py:102,
    src/systems/strategic_systems/intelligence.py:1342,1445 (line numbers re-verified this
    session — the ledger's prior L1266/L1340 citations had already drifted from unrelated
    changes and are corrected here alongside the relocation).
```
The `test_path` (already-existing `test_spawn_lock_condition.py` test) is unchanged per
investigation.md's Parity Ledger Overlap section — it still exercises the behavior correctly via
`AdventureDecisionPhase.apply()`'s unmodified `phase.py:151` gate.
- **Other writers to this shared YAML file:** `strategic_cognition.yaml` also holds STRAT-185,
  STRAT-186, STRAT-187 (the P0 entries governing the locked-branch gate this ticket's check sits
  inside, both `test_path: null` today) and STRAT-237 (the entry immediately following STRAT-236,
  confirmed by grep this session). This step edits **only** STRAT-236's `text`/`v2_evidence` fields
  — it must not renumber, reformat, or otherwise touch STRAT-185/186/187/STRAT-237 or any other
  entry in the file. No other ticket is concurrently editing this file in this session (confirmed —
  it is not listed as a modified file in the current session's git status), so there is no
  merge/ordering race to reconcile.

**Do NOT touch:** STRAT-185/STRAT-186/STRAT-187's own entries (out of scope per this ticket's Out of
Scope and investigation.md — closing their `test_path: null` gap is explicitly not required by this
ticket's ACs, even though Step 6's new test would be a reasonable future candidate). Do NOT touch any
other subsystem's parity ledger file.

**Verify:** `tests/tools/test_parity_ledger_scan.py` (schema/structure validator) still passes,
confirming the YAML stays well-formed after the edit. Semantic correctness of the prose is verified
by direct review (parity-updater agent / Finalize), not by an automated content assertion.

## Scope Guards

- Do not touch `AdventureDecisionPhase`'s class body (`phase.py:99-`) beyond the one call-site edit
  at `phase.py:192-194` (Step 3) needed to pass `state=state`, and the import/function-removal edits
  in Step 1 (`phase.py:21`, `phase.py:27-46`).
- Do not perform any part of `DELETE-ADVENTURE-DECISION-PHASE`'s (C3) job: do not delete
  `AdventureDecisionPhase`, do not relocate `_resolve_cognition_profile_id`
  (`phase.py:49-80`) or `_supports_adventure_routing` (`phase.py:83-96`).
- Do not touch `STRAT-185`/`STRAT-186`/`STRAT-187`'s parity ledger entries or attempt to close their
  `test_path: null` gap.
- Do not touch `AdventureGoalScorer`'s already-landed materialization branch
  (`intelligence.py:1402-1429`, the `GoalKind.ADVENTURE_ROUTE` handling from
  `TCK-20260811-ADVENTURE-GOAL-SCORER`).
- Do not fold the new `_threat_resolved` check into the `kind == "detour"` branch or the
  percentage/urgency-floor `else` branch (`intelligence.py:986-999`) as a second special case — the
  design doc explicitly rejects this shape.
- Do not edit any of the 27 pre-existing direct `evaluate_project_switch()` test call sites in
  `test_score_normalization.py`, `test_interruption_resistance.py` (existing tests only — new tests
  are additive), `test_project_continuity.py`, `test_strategic_reprioritization.py`,
  `test_quest_activation_pathway.py`.
- Do not modify `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` — no
  change is required (confirmed: its AST guard matches callee name only, not arity).
- Do not modify `tests/unit/systems/test_spawn_lock_condition.py` — it remains STRAT-236's
  unmodified `test_path`.
- Do not attempt to "optimize away" `phase.py:151`'s redundant same-tick evaluation of
  `_threat_resolved` against the new check inside `evaluate_project_switch()` — the ticket
  explicitly discloses and pre-authorizes this redundancy as harmless and out of scope.
- Do not unify the `GoalKind`/`ProjectKind` vocabulary split (tracked separately under D22/C4).
- Do not rewrite `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
  wholesale; it is a point-in-time design record not owned by this ticket. (Its own stale
  `:1341`/`:1422`/`:928-932` line citations may optionally be corrected inline as a should-fix, but
  this is not a required step and is not tracked in the Acceptance Criteria Map below.)

## Dependency Map

- Step 1 (relocate `_threat_resolved`) must land before Step 2 — Step 2's widened condition calls
  `_threat_resolved`, which must already exist in `intelligence.py`.
- Step 2 (signature + condition widening) must land before Step 3 — passing `state=state` to a
  signature that does not yet accept it is a `TypeError`.
- Steps 1–3 must all land before Steps 4, 5, and 6 — every new test in those steps calls
  `evaluate_project_switch(..., state=state)` or exercises the relocated `_threat_resolved`, and
  would fail against the pre-change code.
- Steps 4, 5, and 6 are independent of each other (different files/test functions) and can be done
  in any order relative to one another, but all depend on Steps 1–3.
- Step 7 (parity ledger) has no code dependency on Steps 1–6, but should land last so its
  `v2_evidence` line-number citations describe the actual final state of the relocated code rather
  than an intermediate one.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: `evaluate_project_switch()`'s signature gains `state: AuthoritativeState`; all 3 real production call sites thread it; no behavior change on the raw/unlocked comparison path | Step 2 (signature), Step 3 (3 call sites) | `test_evaluate_project_switch_signature_accepts_state_kwarg`, `test_evaluate_project_switch_unlocked_path_identical_with_and_without_state`, `test_three_production_call_sites_thread_state_argument` (Step 4); full 27-call-site regression surface across `test_score_normalization.py`, `test_interruption_resistance.py`, `test_project_continuity.py`, `test_strategic_reprioritization.py`, `test_quest_activation_pathway.py` staying green unmodified |
| AC2: Locked current project + entity HP>80% + no hostile within radius 10.0 → lock treated as expired, falls to raw comparison, byte-identical to today's `AdventureDecisionPhase`-only behavior for adventure-originated projects | Step 1 (relocation), Step 2 (widened condition) | `test_evaluate_project_switch_locked_project_released_when_threat_resolved` (Step 5); `tests/unit/systems/test_spawn_lock_condition.py::TestLockEarlyRelease::test_lock_released_when_hp_high_and_no_hostiles` (unmodified regression confirmation) |
| AC3: A COMBAT_RETREAT/RECOVER-kind project locked via a non-adventure system, with threat resolved, is now also early-released — new regression test required | Step 2 (widened condition, generalized beyond adventure domain) | `test_combat_retreat_project_locked_via_system_b_early_released_when_threat_resolved` and `test_combat_retreat_project_locked_via_system_b_retained_when_threat_still_active` (Step 6, new file `tests/unit/strategic/test_threat_resolved_lock_release.py`) |
| AC4: STRAT-236's `text` AND `v2_evidence` fields in `docs/parity_ledger/strategic_cognition.yaml` both cite the new location and generalized scope | Step 7 | `tests/tools/test_parity_ledger_scan.py` (schema validity only); semantic correctness verified by direct review of the YAML diff, not an automated test |

## Anti-Drift Notes

- **The require-vs-default `state` design decision is explicitly resolved by this plan, not left
  open**: `state: Optional[AuthoritativeState] = None`, with `_threat_resolved` only invoked when
  `state is not None` (Python's `and` short-circuit in `threat_resolved = state is not None and
  _threat_resolved(entity, state)` guarantees `_threat_resolved` is never called with `state=None`,
  avoiding an `AttributeError` inside `SpatialQueryService.nearby_entities`/`WorldIndexService`).
  This is the single highest-leverage decision in this ticket — implementing it as a *required*
  parameter instead would silently flip lock-retention assertions across the 27 pre-existing direct
  call sites, per investigation.md's evidence (`V2EntityBuilder`'s default `CombatComponent` is
  `hp=100/max_hp=100`, HP ratio 1.0, which alone satisfies half of `_threat_resolved`'s condition,
  combined with an empty `state.entities` satisfying the other half).
- **The widened condition touches only the outer gate, and `threat_resolved` must be computed
  lazily *inside* it, not above/outside it.** `intelligence.py:986-999` (the `kind == "detour"`
  bypass and the percentage/urgency-floor `else` branch, now nested one level deeper under a new
  `if not threat_resolved:`) must remain byte-identical. If Implement finds itself editing anything
  inside that block for this ticket, that is a signal the wrong shape is being built. Separately:
  `threat_resolved = state is not None and _threat_resolved(entity, state)` must be the **first
  statement inside** `if current.lock_until_tick > current_tick:`, not a statement that runs before
  that `if` (and not inlined into the `if`'s own condition as `... and not _threat_resolved(...)`
  either) — `_threat_resolved` calls `SpatialQueryService.nearby_entities()`, an O(radius²) scan, and
  computing it outside/above the lock-active gate would run that scan unconditionally on every
  `evaluate_project_switch()` call for any entity with a real `state` — including the common,
  unlocked-project case at all 3 real production call sites — instead of only when the current
  project is actually locked.
- **`phase.py:151`'s gate and the new `evaluate_project_switch()` check will redundantly evaluate
  `_threat_resolved()` twice on the same tick** when an adventure-originated candidate makes it past
  `phase.py:151` and reaches `evaluate_project_switch()`. This is real, already traced in
  investigation.md, and explicitly pre-authorized by the ticket as harmless — do not attempt to
  deduplicate or "optimize" it as part of this ticket.
- **`_score_scale_max()` classifies by enum *class* identity, not string value** — `ProjectKind` vs.
  `GoalKind` share some string values (e.g. both have a `"social"`/`"harvesting"`-shaped member) but
  are different Python classes. Step 6's new test must construct the current project with the actual
  `GoalKind.COMBAT_RETREAT` (or `GoalKind.RECOVER`) enum member, never the raw string
  `"combat_retreat"`, or the test would silently misrepresent the System-B scenario it's meant to
  prove. In AC3's actual scenario this classification is moot in practice (the locked-branch
  percentage path is never reached once `_threat_resolved` short-circuits the outer condition) but
  gets it wrong would still make the test's *setup* semantically incorrect.
- **`SpatialQueryService.nearby_entities()` itself needs no changes** — `_threat_resolved()` calls it
  with the exact same three arguments (`state`, `hero.navigation.position`, `radius=10.0`) both
  before and after relocation; only which module imports `SpatialQueryService` changes.
- **This ticket does not close STRAT-185/186/187's `test_path: null` gap.** Step 6's new test is a
  reasonable *candidate* `test_path` for one of those entries in a future ticket, but wiring it in as
  such here would be scope creep beyond this ticket's own 4 ACs — leave that decision to whichever
  future ticket owns it.
- **`intelligence.py`'s import of `src.domains.adventure.mapper` (line 79) already exists** — Step
  1's new `phase.py` → `intelligence.py` import direction does not create or risk a new import
  cycle; confirmed by reading `mapper.py`'s own imports this session (limited to `src.core.strategic`
  and `src.domains.adventure.schema`, no back-reference to `phase.py`).
