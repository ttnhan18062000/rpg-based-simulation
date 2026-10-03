---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS
artifact_type: plan
tags: [lifecycle, adventure]
---

# Implementation Plan — TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS

## Summary

Add a new durable, plural `dependent_entity_ids` field to `LifecycleComponent` (following the
exact `heirlooms`/`heirlooms_add` list-field write-path pattern, not a reuse of the singular,
death-only `heir_entity_id`), and a new post-clamp additive bias block (§9b) in
`AdventureRouteScorer.score()` that reads `entity.lifecycle.dependent_entity_ids` directly (never
a new optional scorer parameter) to lower `HUNT_WEAK_ENEMY` scores and raise
`RECOVER`/`RETURN_TOWN` scores when an entity has at least one dependent. No trigger/registration
system is built — dependents are established only via the builder, for tests — and
birth-triggered parental auto-registration is explicitly documented as deferred to the
Reproduction epic. Docs (`04_strategic_cognition.md` §6.13, `05_world_evolution.md` Succession
section, `docs/core/entities.md` component table) and a new parity ledger entry `SOC-262` are
updated in the same session per the Authoritative Mechanics Rule.

## Decisions (resolving the four open questions)

### Decision 1 — Durable field: new `LifecycleComponent.dependent_entity_ids`, not `heir_entity_id` reuse, not `SocialBond`

`heir_entity_id: Optional[int] = None` (`src/core/state.py:161`) is confirmed singular and
read exactly once, post-death, by `LifecycleSystem._select_default_heir()`
(`src/systems/lifecycle_systems/lifecycle.py:21-35`) — giving it a second, pre-death,
alive-relevance meaning would be real semantic drift (investigation's own argument, confirmed by
direct read). `SocialBond`/`RelationshipRole` (`src/core/models/social.py`) has only
`NEUTRAL`/`FRIEND`/`RIVAL` — no responsibility-classification axis, and CLAUDE.md's hazard list
explicitly forbids overloading it.

Decision: add `dependent_entity_ids: list[int] = field(default_factory=list)` to
`LifecycleComponent`, immediately after `parent_b_entity_id` (`src/core/state.py:164`) and before
`birth_tick` (`src/core/state.py:165`) — mirroring `heirlooms: list[str] = field(default_factory=list)`
(`src/core/state.py:162`), the closest existing plural-field precedent on the same dataclass, in
type shape (`list[X]`), default (`field(default_factory=list)`), and canonicalization
(`to_canonical_dict()` sorts it: `src/core/state.py:183`, `"heirlooms": sorted(list(self.heirlooms))`).

Write path (mirrors `heir_entity_id`'s own precedent exactly, per investigation.md and confirmed
by direct read of `src/core/updates.py:433-478` and `src/engine/patches.py:69-97`):
- `LifecycleUpdate.dependent_entity_ids_add: list[int] = field(default_factory=list)`
  (`src/core/updates.py`, new field alongside `heirlooms_add: list[str] = field(default_factory=list)`
  at `src/core/updates.py:443`), merged via list-extend in `LifecycleUpdate.merge()`
  (`src/core/updates.py:471`, `if other.heirlooms_add: changes["heirlooms_add"] = self.heirlooms_add + other.heirlooms_add`
  is the exact pattern to copy) and included in `is_noop()` (`src/core/updates.py:454-459`).
- `LifecyclePatch.apply()` (`src/engine/patches.py:69-97`) extends the field the same way
  `heirlooms` is extended at `src/engine/patches.py:76-78` (`new_heirlooms = list(new_lifecycle.heirlooms); new_heirlooms.extend(u_life.heirlooms_add)`),
  writing the result into the `replace(new_lifecycle, ...)` call at line 84's sibling position.

This is a genuinely new field, never a bare mutation of frozen state — satisfies CLAUDE.md's
Durable State Rule and the Authoritative Mutation Pipeline Contract.

### Decision 2 — Read `entity.lifecycle.dependent_entity_ids` directly in `score()`; no new parameter

Confirmed by direct read of the real, sole live call chain:
- `AdventureGoalScorer.score(self, entity: EntityState, state: AuthoritativeState)` (`src/ai/goals/adventure_scorer.py:96`)
  calls `AdventureDecisionService.decide(entity, candidates, tick=state.tick, resource_nodes=state.resource_nodes, faction_directives=None, factions=state.factions)`
  (`src/ai/goals/adventure_scorer.py:137-144`) — note `group` is not passed here at all (defaults
  to `None` inside `decide()`), and `faction_directives` is hardcoded `None` (the confirmed-dead
  pattern investigation.md warns against).
- `AdventureDecisionService.decide()` (`src/domains/adventure/service.py:31-38`) calls
  `AdventureRouteScorer.score(entity, cand, resource_nodes=resource_nodes, faction_directives=faction_directives, factions=factions)`
  (`src/domains/adventure/service.py:73-78`) — `entity` is passed positionally, unconditionally,
  at every call; `group` is never passed by this live path either.

`entity: EntityState` is the only argument confirmed unconditionally populated on every real call
in production. Decision: the new §9b block reads `entity.lifecycle.dependent_entity_ids` directly
off the already-passed `entity` argument — no new `AdventureRouteScorer.score()` parameter is
added. This makes the mechanic live-wired for free, avoiding the `faction_directives`/`group`
dead-code trap.

Note: `score()` has no `state`/world-truth parameter at all (confirmed: `src/domains/adventure/scoring.py:39-49`
signature), so there is no way to check a listed dependent's liveness from inside `score()`
without adding exactly the kind of new parameter this decision rejects. The bias is therefore
keyed on non-empty `dependent_entity_ids` alone (presence, not liveness) — consistent with this
file's own documented design philosophy of reading only subjective/entity-owned state, never
omniscient world truth (`src/domains/adventure/scoring.py:6-13` docstring).

### Decision 3 — RouteFamily members: `HUNT_WEAK_ENEMY` (risky), `RECOVER` + `RETURN_TOWN` (recovery-oriented)

`RouteFamily` has 16 members (`src/domains/adventure/schema.py:16-33`), confirmed by direct read.
`HUNT_WEAK_ENEMY` is the ticket's own named example for "risky." For "return/recovery-oriented"
the AC uses "and/or" (not a full enumeration) — this plan implements both the risky-lowering and
the recovery-raising halves, using the two schema members whose names directly denote
returning/recovering: `RECOVER = "recover"` and `RETURN_TOWN = "return_town"`
(`src/domains/adventure/schema.py:18,29`). `SCOUT_LOCATION`/`GATHER_RESOURCE` are explicitly
excluded (not named by the ticket, and already carry other personality-bias terms at
`src/domains/adventure/scoring.py:214-219` that this ticket must not perturb).

### Decision 4 — Non-parental dependent construction: builder-only, no trigger system

No code today marks any entity as "dependent-eligible" (confirmed: `LifeStage.ELDER` per
`docs/mechanics/05_world_evolution.md:210-215` is a stat-modifier bracket on the elder itself, not
a caretaker-relationship marker). Per the ticket's own Out of Scope, this plan builds no
birth-triggered or life-stage-triggered auto-registration system. Construction path for tests/demo:
`V2EntityBuilder.lifecycle(dependent_entity_ids=[...])` (extending
`src/core/builder.py:576-620`, mirroring the existing `heirlooms: Optional[List[str]] = None`
kwarg at line 587 and its `_copy_list(...)` handling at line 606) or
`V2EntityBuilder.replace_lifecycle(LifecycleComponent(dependent_entity_ids=[...]))`
(`src/core/builder.py:795`, already generic — no change needed). This matches
`test_scoring_plan_bonus.py`'s own `_build_entity()` helper pattern
(`tests/unit/domains/adventure/test_scoring_plan_bonus.py:20-30`, `V2EntityBuilder(1)` + chained
setters).

**Deferred follow-up (documented, not built):** birth-triggered parental dependent
auto-registration (a newborn automatically becomes the parent's dependent via
`parent_a_entity_id`/`parent_b_entity_id`, added by the sibling
`TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`) is out of scope for this ticket and is blocked on
`TCK-20260902-EPIC-RPG-M3-REPRODUCTION`'s birth-record schema maturing further. This plan does not
wire `build_parent_bond_updates_for_birth()` or any birth path to the new field — Step 6 records
this explicitly in both mechanics docs.

## Steps

### Step 1 — Add `dependent_entity_ids` durable field to `LifecycleComponent`/`LifecycleUpdate`/`LifecyclePatch.apply()`
**Files:** `src/core/state.py`, `src/core/updates.py`, `src/engine/patches.py`

**Change:**
- `src/core/state.py`: add `dependent_entity_ids: list[int] = field(default_factory=list)` to
  `LifecycleComponent` (line ~164, between `parent_b_entity_id` and `birth_tick`). Add
  `"dependent_entity_ids": sorted(list(self.dependent_entity_ids)),` to `to_canonical_dict()`
  (line ~183 area), mirroring the `heirlooms` sort exactly (`src/core/state.py:183`).
- `src/core/updates.py`: add `dependent_entity_ids_add: list[int] = field(default_factory=list)`
  to `LifecycleUpdate` (line ~443, alongside `heirlooms_add`). Add
  `and not self.dependent_entity_ids_add` to `is_noop()` (line ~454-459). Add
  `if other.dependent_entity_ids_add: changes["dependent_entity_ids_add"] = self.dependent_entity_ids_add + other.dependent_entity_ids_add`
  to `merge()` (line ~471, mirroring the `heirlooms_add` line exactly).
- `src/engine/patches.py`: in `LifecyclePatch.apply()` (lines 69-97), extend
  `dependent_entity_ids` the same way `heirlooms` is extended (lines 76-78): build
  `new_dependents = list(new_lifecycle.dependent_entity_ids); new_dependents.extend(u_life.dependent_entity_ids_add)`
  and pass `dependent_entity_ids=tuple(new_dependents)` into the `replace(new_lifecycle, ...)` call
  (line 84's sibling position), matching `heirlooms=tuple(new_heirlooms)`'s existing precedent
  exactly (same list-typed-field-assigned-as-tuple pattern already in use — do not "fix" this
  inconsistency, match it).

**Other writers to this shared resource (`LifecycleUpdate`/`LifecyclePatch.apply()`), confirmed by
direct grep of every `LifecycleUpdate(` construction site in `src/`:**
- `src/world/reproduction_humanoid.py:102-103` — writes only `reproduction_cooldowns_add`.
- `src/engine/movement.py:240` — writes age/death-related fields (not enumerated further here;
  does not touch heirlooms/dependents).
- `src/engine/domain/combat_actions.py:103`, `src/engine/domain/aoe_actions.py:74`,
  `src/engine/domain/skill_actions.py:124` — death-path writers (`death_tick_set`/`death_reason_set`
  class fields), triggered by combat/AoE/skill damage resolution.
- `src/systems/lifecycle_systems/lifecycle.py:93,108` — `resolve_lifecycle()`'s own
  `heir_entity_id_set`/`heirlooms_add`/death writes.

None of these construct a `LifecycleUpdate` that sets `dependent_entity_ids_add` — each passes
only its own specific kwargs, so the new field defaults to `[]` (a no-op) on every one of their
calls automatically, exactly like `heirlooms_add` already does for all of them today. Because
`LifecyclePatch.apply()` performs one `dataclasses.replace()` merging all named fields
independently, adding the new field is purely additive: it cannot collide with, reorder, or
double-count any of these other writers' own fields. No ordering/race risk exists because all
`LifecycleUpdate` fields for a given entity within one tick are merged via `LifecycleUpdate.merge()`
before `LifecyclePatch.apply()` runs once per entity (existing pipeline invariant, unchanged by
this step).

**Do NOT touch:** `heir_entity_id`'s own read/write logic (`_select_default_heir()`,
`resolve_lifecycle()`'s heir-assignment block) — this is a new, independent field, not a
replacement.

**Verify:** New Test #5 from test_plan.md (`test_dependent_field_round_trip`,
`test_dependent_field_applied_via_authoritative_patch` in `tests/unit/progression/test_lifecycle.py`).

---

### Step 2 — Extend `V2EntityBuilder.lifecycle()` with `dependent_entity_ids` kwarg
**Files:** `src/core/builder.py`

**Change:** Add `dependent_entity_ids: Optional[List[int]] = None` parameter to
`V2EntityBuilder.lifecycle()` (`src/core/builder.py:576-620`), following the exact `heirlooms`
handling: add to the `updates` dict as
`"dependent_entity_ids": _copy_list(dependent_entity_ids) if dependent_entity_ids is not None else None`
(mirroring line 606). No change needed to `replace_lifecycle()` (`src/core/builder.py:795`, already
accepts a full `LifecycleComponent`) or `_lifecycle_to_dict()` (`src/core/builder.py:851-852`,
generic reflection via `_to_dict()`, requires no per-field update).

**Do NOT touch:** `birth_record()` (`src/core/builder.py:622+`) or
`build_parent_bond_updates_for_birth()` — these implement the sibling REPRODUCTION ticket's
child→parent direction and must not be wired to the new dependent field (Decision 4's deferred
follow-up).

**Verify:** Exercised transitively by Step 4's new scoring tests, which construct entities via
this builder method.

---

### Step 3 — Add `dependent_bias` bias term to `AdventureRouteScorer.score()` (§9b)
**Files:** `src/domains/adventure/schema.py`, `src/domains/adventure/scoring.py`

**Change:**
- `src/domains/adventure/schema.py`: add `dependent_bias: float = 0.0` to `AdventureRouteOption`
  (line ~73, after `memory_adjustment`), following the exact pattern of the other five dedicated
  trace fields already on this dataclass (`personality_bias`, `confidence_bonus`, `risk_penalty`,
  `blocker_penalty`, `plan_advance_bonus`, `memory_adjustment` — `src/domains/adventure/schema.py:68-73`).
  This gives the new term a dedicated, debuggable trace field matching the majority pattern
  investigation.md recommended, rather than §9's no-trace-field exception.
- `src/domains/adventure/scoring.py`: add a new `§9b` block immediately after the existing §9
  escort-scoring block (after line 368, before the `return dataclasses.replace(...)` at lines
  370-381):
  ```python
  # ── 9b. Personal Dependents Route Bias (SOC-262) ─────────────────────────
  # Reads entity.lifecycle.dependent_entity_ids directly (never a new optional scorer
  # parameter) -- entity is the only argument confirmed unconditionally passed at every
  # live call site (service.py:74, adventure_scorer.py:138); group/faction_directives are
  # not always threaded through and must not be the read source (see plan.md Decision 2).
  dependent_bias = 0.0
  if entity.lifecycle.dependent_entity_ids:
      if route.family == RouteFamily.HUNT_WEAK_ENEMY:
          dependent_bias = -2.0
      elif route.family in (RouteFamily.RECOVER, RouteFamily.RETURN_TOWN):
          dependent_bias = 1.0
      if dependent_bias != 0.0:
          final_score = round(max(0.0, final_score + dependent_bias), 4)
  ```
  Add `dependent_bias=round(dependent_bias, 4),` to the `dataclasses.replace(...)` call
  (after `blocker_penalty=round(blocker_penalty, 4),` at line 380).

**Other writers to `final_score` in this same function (shared local, not a durable resource, but
must be checked for ordering/interaction per fact-verification rule #2):** §7's clamp
(`src/domains/adventure/scoring.py:333-334`), §8's two multiplicative group-synergy adjustments
(`src/domains/adventure/scoring.py:336-355`, SOC-229), and §9's escort additive adjustment
(`src/domains/adventure/scoring.py:357-368`, SOC-230) all mutate the same `final_score` local,
sequentially, within one `score()` call. Placing §9b strictly after §9 means it operates on
whatever `final_score` §9 already produced — this is safe and intentional: both §9 and §9b are
independent flat additive/floored adjustments keyed on disjoint conditions (`group.escort_target_id`
for §9 vs. `entity.lifecycle.dependent_entity_ids` for §9b), so an entity that is both escorted and
has a dependent receives both adjustments, in sequence, with no double-counting or override —
exactly the outcome New Test #4 (`test_dependent_bias_independent_of_other_additive_terms`) and
the anti-drift guard in test_plan.md require. No other function or thread writes `final_score`;
it is function-local to this single `score()` call.

**Do NOT touch:** the §9 escort-scoring block itself (lines 357-368) — explicit ticket Out of
Scope; add only a new, separate `if` clause. Do not touch §4's personality-bias block
(lines 206-223) — a dependent bias is a fact about durable state, not a subjective personality
trait, so it does not belong pre-clamp alongside §4 (investigation's explicit recommendation).

**Verify:** New Test #1, #2, #3 from test_plan.md (`test_dependent_route_bias_lowers_risky_route_score`,
`test_dependent_route_bias_raises_recovery_route_score`, `test_dependent_route_bias_zero_when_no_dependent`).

---

### Step 4 — New test file `tests/unit/domains/adventure/test_scoring_dependent_bias.py`
**Files:** `tests/unit/domains/adventure/test_scoring_dependent_bias.py` (new)

**Change:** Implement all four new tests from test_plan.md, following
`test_scoring_plan_bonus.py`'s `_build_entity()`/`_route()` helper pattern
(`tests/unit/domains/adventure/test_scoring_plan_bonus.py:20-37`), using
`V2EntityBuilder(1).lifecycle(dependent_entity_ids=[2])` (Step 2's new kwarg) to construct the
with-dependent entity and an otherwise-identical entity without it for baseline comparison:
1. `test_dependent_route_bias_lowers_risky_route_score` — assert
   `result_with_dependent.score < result_without_dependent.score` on `HUNT_WEAK_ENEMY`, and assert
   `result_with_dependent.dependent_bias == -2.0` directly.
2. `test_dependent_route_bias_raises_recovery_route_score` — same shape, `RECOVER` and/or
   `RETURN_TOWN`, asserting `dependent_bias == 1.0`.
3. `test_dependent_route_bias_zero_when_no_dependent` — entity with `dependent_entity_ids=[]`
   (default/unset) produces `dependent_bias == 0.0` and an identical `.score` to a pre-this-ticket
   baseline call.
4. `test_dependent_bias_independent_of_other_additive_terms` — combine with `plan_advance_bonus`
   (reuse `_plan_with_head()` helper from `test_scoring_plan_bonus.py` if importable, or an
   equivalent local `ProgressionPlan`) on the same route, asserting
   `result.score == baseline + dependent_delta + plan_advance_bonus` (all via `abs(...) < 0.01`
   comparisons per test_plan.md's anti-drift guidance, never hardcoded absolute scores).

**Do NOT touch:** any existing file in `tests/unit/domains/adventure/` — this is a new file only.

**Verify:** `pytest tests/unit/domains/adventure/test_scoring_dependent_bias.py -v` plus the full
regression surface: `pytest tests/unit/domains/adventure/ -v` (all pre-existing files in this
directory, per test_plan.md's Regression Surface list, must keep passing unmodified).

---

### Step 5 — Write-path tests for the new durable field
**Files:** `tests/unit/progression/test_lifecycle.py`

**Change:** Add `test_dependent_field_round_trip` (canonical-dict serialization of
`dependent_entity_ids`, matching `LifecycleComponent.to_canonical_dict()`'s existing
round-trip-test pattern in this file) and `test_dependent_field_applied_via_authoritative_patch`
(asserts the field is only ever set via `LifecycleUpdate.dependent_entity_ids_add` →
`LifecyclePatch.apply()`, mirroring this file's existing assertions for `heir_entity_id_set`, e.g.
around line 165's `assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 2` pattern).

**Do NOT touch:** any of the pre-existing 24+ tests in this file (per test_plan.md, they must
continue passing unmodified) — this step only appends new test functions.

**Verify:** `pytest tests/unit/progression/test_lifecycle.py -v`.

---

### Step 6 — Documentation: `04_strategic_cognition.md`, `05_world_evolution.md`, `docs/core/entities.md`, parity ledger `SOC-262`
**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/mechanics/05_world_evolution.md`,
`docs/core/entities.md`, `docs/parity_ledger/social_narrative.yaml` (via
`tools/parity_ledger_writer.py:write_entry()`, never a raw Edit)

**Change:**
- `docs/mechanics/04_strategic_cognition.md`: insert new `### 6.13 Personal Dependents Route Bias
  (SOC-262)` subsection after `### 6.12 Capability-Driven Confidence Bonus` (ends at line ~848) and
  before `## 7. Party Composition & Formation Scoring` (line 850), following `### 6.9 Escort Route
  Scoring (SOC-230)`'s exact structure (`docs/mechanics/04_strategic_cognition.md:700-716`): a
  table of route family → adjustment → rationale, a "Source:" citation line, and — critically — an
  explicit paragraph stating that birth-triggered parental auto-registration is deferred to
  `TCK-20260902-EPIC-RPG-M3-REPRODUCTION` and not implemented by this mechanic (Decision 4).
- `docs/mechanics/05_world_evolution.md`: insert a new `### Personal Dependents (Non-Parental)
  (TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS)` subsection immediately after `### Succession —
  Default Heir Assignment` (which ends at line ~206, before `### Migration Law`), documenting the
  new `LifecycleComponent.dependent_entity_ids` field and its `LifecycleUpdate`/`LifecyclePatch.apply()`
  write path (cross-referencing 04's §6.13 for the scoring effect, matching the Succession
  section's own precedent of cross-referencing 04§7.2 at its end). Same explicit deferred-follow-up
  statement as above.
- `docs/core/entities.md`: add `dependent_entity_ids` to the Lifecycle component-table row
  (line 52) field list, alongside the existing `heir_entity_id`, `heirlooms`, etc.
- `docs/parity_ledger/social_narrative.yaml`: add entry `id: SOC-262` via
  `tools/parity_ledger_writer.py:write_entry("social_narrative.yaml", entry)` — never a raw
  YAML Edit (this repo's sanctioned path per CLAUDE.md and the memory note on raw-YAML-rewrite
  corruption risk). Entry fields, mirroring `SOC-261`'s shape
  (`docs/parity_ledger/social_narrative.yaml:3835-3864`): `text` describing the new field +
  scoring bias + the explicit "birth-triggered parental auto-registration deferred" note,
  `status: verified`, `priority: P2` (matches this ticket's own P2), `v2_evidence` citing
  `src/core/state.py` (LifecycleComponent.dependent_entity_ids), `src/core/updates.py`
  (LifecycleUpdate.dependent_entity_ids_add), `src/engine/patches.py` (LifecyclePatch.apply()),
  `src/domains/adventure/scoring.py` §9b, `src/domains/adventure/schema.py`
  (AdventureRouteOption.dependent_bias), `proof_type: regression`,
  `test_path: tests/unit/domains/adventure/test_scoring_dependent_bias.py::test_dependent_route_bias_lowers_risky_route_score`.

**Do NOT touch:** `docs/guidelines/intentional_divergences.md` (not applicable — this is a new
mechanic, not a divergence, per investigation.md's explicit conclusion) or any existing SOC-230/
SOC-245/SOC-259/SOC-261 entry's own `text`/`status` (only a new entry is added).

**Verify:** No automated test for docs; confirm via `python3 tools/parity_ledger_writer.py` (or
equivalent invocation) that `write_entry()` succeeds and the derived parity index rebuilds without
error (the function's own postcondition, per `tools/parity_ledger_writer.py:90-119`).

---

### Step 7 — Confirm the pinned architecture guard passes unmodified
**Files:** none (verification-only step)

**Change:** No code change expected. Run
`pytest tests/architecture/test_adventure_route_score_max_unchanged.py -v` after Steps 1-3 land.
If it fails, the new bias term has been implemented in a way that touches
`_ADVENTURE_ROUTE_SCORE_MAX` (2.9, `src/systems/strategic_systems/intelligence.py`) or
`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` (2.4, `src/ai/goals/adventure_scorer.py`) — this is a
scope violation to fix in Step 3 (e.g. reduce the flat bias magnitude or re-check placement), never
a test to edit (Gate Integrity rule, CLAUDE.md). SOC-230's own precedent (`+3.0`/`-1.0` already
coexisting with this constant unmodified) establishes that flat additive/floored terms of this
magnitude are safe.

**Do NOT touch:** `tests/architecture/test_adventure_route_score_max_unchanged.py` itself, or
either pinned constant.

**Verify:** `pytest tests/architecture/test_adventure_route_score_max_unchanged.py -v` passes with
zero diff to the test file.

## Scope Guards

- Do NOT build birth-triggered parental dependent auto-registration (newborn → parent's
  `dependent_entity_ids`) — explicitly deferred to `TCK-20260902-EPIC-RPG-M3-REPRODUCTION`. No
  wiring of `build_parent_bond_updates_for_birth()` or `birth_record()` to the new field.
- Do NOT touch `heir_entity_id`'s own read/write logic — `_select_default_heir()`,
  `resolve_lifecycle()`'s heir-assignment block, or the `heir_entity_id_set` write path — the new
  field is additive and independent.
- Do NOT touch the §9 escort-scoring block (SOC-230, `src/domains/adventure/scoring.py:357-368`)
  itself — add only a new, separate `if` clause alongside it.
- Do NOT touch `_ADVENTURE_ROUTE_SCORE_MAX` (2.9) or `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` (2.4)
  — both pinned by architecture tests.
- Do NOT reuse or extend `RelationshipRole`/`SocialBond` to mean "dependent."
- Do NOT reuse or extend `ContractKind`/Marriage's spousal-protection hook (idea 33) — kept
  distinct per ticket Out of Scope.
- Do NOT add a new `AdventureRouteScorer.score()` parameter for this mechanic — must read directly
  off `entity`.
- Do NOT edit `docs/guidelines/intentional_divergences.md` — not applicable.
- Do NOT modify any pre-existing parity ledger entry's `text`/`status` (SOC-230/SOC-245/SOC-259/
  SOC-261) — only append the new SOC-262 entry.

## Dependency Map

- Step 1 (durable field) has no dependencies — can start immediately.
- Step 2 (builder kwarg) depends on Step 1 (needs the field to exist on `LifecycleComponent`).
- Step 3 (scoring bias) depends on Step 1 (reads `entity.lifecycle.dependent_entity_ids`) but not
  on Step 2 (scoring reads the field directly; the builder kwarg is only a test-construction
  convenience).
- Step 4 (new scoring tests) depends on Steps 2 and 3 (needs both the builder kwarg to construct
  entities and the scoring bias to exist).
- Step 5 (write-path tests) depends on Step 1 only.
- Step 6 (docs + parity ledger) depends on Steps 1 and 3 being finalized (docs describe the real
  field name and bias magnitudes).
- Step 7 (architecture guard confirmation) depends on Step 3 being complete; run last.

Steps 1, 5 can proceed in parallel with Step 3 once Step 1 lands, since Step 3 only needs the field
to exist, not the builder kwarg or write-path tests. Steps 2 and 4 are sequential (2 before 4).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A durable "dependent" concept exists on entity state, covering the non-parental case, with a defined write-path through `StateUpdate`/`EntityUpdate` | Step 1 | `test_dependent_field_round_trip`, `test_dependent_field_applied_via_authoritative_patch` (Step 5) |
| `AdventureRouteScorer.score()` gains a new bias term: lower on risky routes and/or higher on return/recovery routes with an active dependent | Step 3 | `test_dependent_route_bias_lowers_risky_route_score`, `test_dependent_route_bias_raises_recovery_route_score` (Step 4) |
| A dedicated unit test asserts the score delta directly, and the pinned architecture guard passes unmodified | Step 4, Step 7 | `tests/unit/domains/adventure/test_scoring_dependent_bias.py`; `tests/architecture/test_adventure_route_score_max_unchanged.py` |
| `docs/mechanics/05_world_evolution.md` and/or `04_strategic_cognition.md` documents the mechanic; a new `SOC-2xx` parity ledger entry references it | Step 6 | Manual doc review; `write_entry()` postcondition (build report succeeds) |
| Birth-triggered parental dependent auto-registration is explicitly documented as deferred/follow-up | Step 6 (both mechanics docs carry the explicit deferred-follow-up paragraph) | Manual doc review |

## Anti-Drift Notes

- **Live-wiring risk (highest-priority hazard):** the new bias term must read
  `entity.lifecycle.dependent_entity_ids` directly, never a new optional `score()` parameter —
  confirmed via direct read that `entity` is the only argument unconditionally passed at every real
  call site, while `group`/`faction_directives` are not (mirrors the confirmed-dead
  `faction_directives` pattern documented in `docs/mechanics/04_strategic_cognition.md` §6.10).
  During Verify, re-confirm by reading `src/ai/goals/adventure_scorer.py`'s live call site that the
  new field is actually reached, not just unit-testable in isolation (test_plan.md's own guidance).
- **§9/§9b independence:** an entity that is both escorted (`group.escort_target_id` set) and has
  a dependent must receive both adjustments, applied sequentially to the same `final_score` local,
  with no override or double-counting — guarded by New Test #4 and the existing
  `test_escort_target_route_scores_above_survival`.
- **No-op guard:** an entity with `dependent_entity_ids == []` (the default) must produce
  `dependent_bias == 0.0` and an identical score to pre-this-ticket behavior — guarded by New
  Test #3. This is the same class of bug the repo has hit before (an always-on or mis-defaulted
  term).
- **Liveness is intentionally not checked:** `score()` has no world-state parameter, so the bias
  fires on mere presence of an id in `dependent_entity_ids`, not on whether that id refers to a
  currently-alive entity. This is a disclosed simplification consistent with the file's own
  "never omniscient world truth" design philosophy — document it in the Step 6 docs update so it
  is not mistaken for an oversight.
- **`heirlooms`/`dependent_entity_ids` tuple-vs-list inconsistency is pre-existing and intentional
  to preserve**: `LifecycleComponent.heirlooms` is typed `list[str]` but `LifecyclePatch.apply()`
  assigns it via `tuple(new_heirlooms)`. Step 1 mirrors this exact inconsistency for
  `dependent_entity_ids` rather than "fixing" it, to stay byte-for-byte consistent with the
  established write-path pattern the implementer is told to copy.
- **Do not let Step 6's docs slip out of the same session** — CLAUDE.md's Authoritative Mechanics
  Rule requires the parity ledger entry and doc update to land together with the code change, not
  as a follow-up.

## Deviations

- **Test phase regression fix (unplanned, outside the 7 steps above):** landing Step 3's §9b block
  broke `tests/unit/domains/faction/test_faction_directive_propagation.py::
  test_guard_patrol_urgency_boosted_by_faction_directive`, a pre-existing test in an unrelated
  suite that this plan's Steps/Regression-Surface list did not anticipate needing changes (its
  Step 4 regression-surface note only covered `tests/unit/domains/adventure/`). Root cause:
  that test's shared `_make_entity()` fixture builds `MagicMock(spec=EntityState)` and never
  configured `entity.lifecycle.dependent_entity_ids`; an unconfigured `MagicMock` attribute is
  truthy by default, so the new §9b block spuriously fired `dependent_bias=-2.0` for
  `HUNT_WEAK_ENEMY`, and combined with the `max(0.0, ...)` floor this zeroed out the faction
  directive's own `+2.0` urgency delta the test asserts. Investigated whether this indicated a
  genuine clamp-ordering defect in `scoring.py`'s `score()` (per the anti-drift note above on
  §9/§9b sequencing) rather than a fixture gap: the per-stage `max(0.0, ...)` floor pattern §9b
  uses is identical to the pre-existing §9 `OWN_SURVIVAL` branch and the step-7 floor, so this is
  existing, intentional formula design (not a defect §9b's placement introduced) — confirmed
  fixture gap. Fix: added `entity.lifecycle.dependent_entity_ids = []` to that test file's
  `_make_entity()` helper (one line, test-only change), matching real production's
  empty-list-by-default behavior. Re-ran the full previously-scoped command
  (`tests/unit/core/ tests/unit/domains/ tests/unit/progression/ tests/architecture/
  tests/unit/social/ tests/integration/optimization/ tests/unit/strategic/ tests/unit/ai/goals/`)
  — 1790 passed, no other regressions. No change was made to `src/domains/adventure/scoring.py`
  beyond what Step 3 already specified.
