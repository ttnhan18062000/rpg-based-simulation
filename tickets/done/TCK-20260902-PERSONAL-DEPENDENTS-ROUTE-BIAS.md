---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS
phase: done
date: 2026-09-02
tags: [lifecycle, adventure]
---

# TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS

## Title
Personal Dependents — new route-scoring bias term so entities with dependents avoid unnecessary risk

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Covers idea 31 (Personal Dependents & Responsibility) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Investigation found the concern's own framing partly stale: `heir_entity_id`'s write-path already fires live today — `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py:21-111`) assigns a default heir automatically on death, landed by `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` (parity entry `SOC-245`, verified). The real unbuilt piece is the route-scoring half: a new bias term in `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py:39-381`) so an entity with an active dependent measurably avoids inherently risky routes. The closest existing precedent is the escort-scoring block (§9, `SOC-230`, lines 357-368) which already biases `PROTECT_TARGET`/`OWN_SURVIVAL` scores based on `group.escort_target_id`. This ticket's full scope (birth-triggered parental dependents) is partially blocked on the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION) — only the non-parental dependent case (e.g. elder/veteran) is buildable standalone today; scope this ticket to that case and treat parental auto-registration as a follow-up once the Reproduction epic's birth-record schema lands.

## Scope
- A durable "dependent" concept on entity state: reuse or extend `heir_entity_id` (`src/core/state.py`, `LifecycleComponent`), or add a new typed field if Plan decides reuse conflates "dependent" with the distinct heir-inheritance concept too much — this is an explicit architecture decision for Plan, not assumed here. Cover at minimum the non-relative/non-parental case (e.g. elder/veteran dependent).
- A new bias term in `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) such that an entity with an active dependent scores measurably lower on inherently risky route families (e.g. `HUNT_WEAK_ENEMY`) and/or higher on return/recovery-oriented routes than an otherwise-identical entity without a dependent — follow the escort-scoring block's (§9, lines 357-368) additive-bias shape as the closest precedent.
- A dedicated unit test asserting the score delta directly, following `tests/unit/domains/adventure/test_scoring_plan_bonus.py`'s pattern.
- Confirm `tests/architecture/test_adventure_route_score_max_unchanged.py` (which pins `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, a separate normalization constant in `intelligence.py`) still passes unmodified after the new bias term is added.

## Out of Scope
- Birth-triggered automatic dependent registration (a newborn child auto-registers as a dependent) — deferred until the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION) lands a birth record to register against. Document this explicitly as a known follow-up, not silently dropped.
- Marriage's spousal-protection hook (idea 33) — explicitly kept distinct per the atlas card; do not conflate with this ticket.
- Any change to the shared trust/escort-scoring logic (`SOC-230`) itself beyond adding a new, independent bias term alongside it.

## Acceptance Criteria
- [x] A durable "dependent" concept exists on entity state (reused `heir_entity_id` or a new typed field, per Plan's decision), covering at minimum the non-parental case, with a defined write-path through `StateUpdate`/`EntityUpdate`.
- [x] `AdventureRouteScorer.score()` gains a new bias term: an entity with an active dependent scores measurably lower on inherently risky route families and/or higher on return/recovery-oriented routes than an otherwise-identical entity without a dependent, all else equal.
- [x] A dedicated unit test in `tests/unit/domains/adventure/` asserts the score delta directly, and `tests/architecture/test_adventure_route_score_max_unchanged.py` still passes unmodified.
- [x] `docs/mechanics/05_world_evolution.md` and/or `docs/mechanics/04_strategic_cognition.md` documents the new mechanic; a new `docs/parity_ledger/social_narrative.yaml` entry (SOC-2xx) references it.
- [x] Birth-triggered parental dependent auto-registration is explicitly documented as deferred/follow-up (not silently omitted), pending the Reproduction epic's birth-record schema.

## Related Tickets
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (DONE — already gives `heir_entity_id_set` its live consumer; the atlas card's "never called by anything live" premise is stale relative to this)
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY (SOC-230 escort scoring — direct architectural precedent to reuse)
- TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5 (architecture guard relevant if scoring.py's formula changes)
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (future dependency for the parental-dependent follow-up, not a blocker for this ticket's own scope)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 31 card)
- docs/mechanics/05_world_evolution.md (Succession — Default Heir Assignment section)
- docs/parity_ledger/social_narrative.yaml (SOC-245, SOC-230)
- CLAUDE.md (Durable State Rule)

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/systems/lifecycle_systems/lifecycle.py
- src/domains/adventure/scoring.py
- src/core/models/social.py

## Assumptions / Open Questions
- Whether to reuse `heir_entity_id` loosely for "dependent" or add a genuinely new field is an open architecture decision for Plan — `heir_entity_id` is a single `Optional[int]`, while "dependent" per the atlas is plural/general (children, wards); reusing `SocialBond` as-is risks conflating dependents with any strong relationship.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS/plan.md`'s
7 steps, no deviations.

1. **Durable field** — added `dependent_entity_ids: list[int] = field(default_factory=list)` to
   `LifecycleComponent` (`src/core/state.py`, between `parent_b_entity_id` and `birth_tick`),
   included in `to_canonical_dict()` sorted like `heirlooms`. Added
   `LifecycleUpdate.dependent_entity_ids_add: list[int]` (`src/core/updates.py`), wired into
   `is_noop()` and `merge()` (additive-list-union, mirroring `heirlooms_add` exactly). Extended
   `LifecyclePatch.apply()` (`src/engine/patches.py`) to extend-then-tuple-assign the field the
   same way `heirlooms` already is.
2. **Builder kwarg** — added `dependent_entity_ids: Optional[List[int]] = None` to
   `V2EntityBuilder.lifecycle()` (`src/core/builder.py`), using the existing `_copy_list()` helper,
   mirroring the `heirlooms` kwarg handling exactly. `birth_record()` and
   `build_parent_bond_updates_for_birth()` were left untouched (Decision 4's deferred follow-up).
3. **Scoring bias** — added `dependent_bias: float = 0.0` trace field to `AdventureRouteOption`
   (`src/domains/adventure/schema.py`) and a new §9b block in `AdventureRouteScorer.score()`
   (`src/domains/adventure/scoring.py`), placed immediately after the existing §9 escort block and
   before the final `dataclasses.replace(...)`. It reads `entity.lifecycle.dependent_entity_ids`
   directly off the always-passed `entity` argument (never a new scorer parameter): `-2.0` (floored
   at 0.0) for `HUNT_WEAK_ENEMY`, `+1.0` for `RECOVER`/`RETURN_TOWN`, no-op otherwise.
4. **New test file** `tests/unit/domains/adventure/test_scoring_dependent_bias.py` — 4 tests
   covering the risky-route delta, the recovery-route delta (both `RECOVER` and `RETURN_TOWN`),
   the no-dependent no-op case, and independence from `plan_advance_bonus` on the same route.
5. **Write-path tests** — added `test_dependent_field_round_trip` and
   `test_dependent_field_applied_via_authoritative_patch` to
   `tests/unit/progression/test_lifecycle.py`, mirroring the file's existing birth-field
   round-trip/authoritative-patch test pattern; also asserts `merge()`'s additive-list-union
   semantics directly.
6. **Docs + parity ledger** — added `04_strategic_cognition.md` §6.13 (Personal Dependents Route
   Bias, SOC-262), a new "Personal Dependents (Non-Parental)" subsection in
   `05_world_evolution.md` immediately after the Succession section (cross-referencing §6.13),
   updated the `docs/core/entities.md` Lifecycle component-table row (also corrected the stale
   `state.py:152-193` line range to `152-195` since the new field shifted it), and wrote a new
   `SOC-262` entry to `docs/parity_ledger/social_narrative.yaml` via
   `tools/parity_ledger_writer.py:write_entry()` (never a raw Edit) — the writer's build-report
   postcondition succeeded (`status: ok`, `entry_count: 2131`). Both mechanics docs explicitly
   state the birth-triggered parental auto-registration deferral to
   `TCK-20260902-EPIC-RPG-M3-REPRODUCTION`.
7. **Architecture guard** — `tests/architecture/test_adventure_route_score_max_unchanged.py` passes
   unmodified (zero diff to the test file); the new §9b block does not touch either pinned
   constant.

All construction sites of `LifecycleComponent(...)` in the repo use keyword args only, so inserting
the new field mid-dataclass carried no positional-argument breakage risk (confirmed by grep before
editing).

### Post-implementation regression fix (Test phase)

The Test phase found `tests/unit/domains/faction/test_faction_directive_propagation.py::
test_guard_patrol_urgency_boosted_by_faction_directive` newly failing after the §9b block landed.
Root cause investigation:

- That test's shared `_make_entity()` helper builds `entity = MagicMock(spec=EntityState)` and
  explicitly configures every attribute the scoring code reads (`identity.role`,
  `identity.personality`, `identity.traits`, `identity.properties`, `attributes.intelligence`,
  `self_model.needs.active_needs`, `combat.alive`, `lifecycle.active`) — this is the file's own
  established, sanctioned pattern (confirmed as the only file in the repo using
  `MagicMock(spec=EntityState)`, so no other suite needed the same follow-up). It simply predates
  the new §9b block and never configured `entity.lifecycle.dependent_entity_ids`.
- An unconfigured `MagicMock` attribute access auto-creates a child `MagicMock`, which is truthy
  by default. `if entity.lifecycle.dependent_entity_ids:` therefore spuriously evaluated `True` for
  this fixture, even though real production `LifecycleComponent.dependent_entity_ids` defaults to
  `[]` (falsy) via `field(default_factory=list)`. For the `HUNT_WEAK_ENEMY` route this fired the
  `-2.0` `dependent_bias`, and combined with the `max(0.0, final_score + dependent_bias)` floor,
  clamped both the baseline (0.0 - 2.0 -> 0.0) and the directive-boosted case (2.0 - 2.0 -> 0.0)
  down to the same 0.0, zeroing out the observed delta the test asserts (expected 2.0, got 0.0).
- Checked whether this is a genuine clamp-ordering defect in `scoring.py`'s `score()` rather than a
  fixture artifact: the per-stage `max(0.0, ...)` floor is a pre-existing, intentional pattern
  already used identically by the §9 escort block's `OWN_SURVIVAL` branch
  (`round(max(0.0, final_score - 1.0), 4)`, line 368) and by the step-7 floor after
  urgency/benefit/risk/blocker combine (line 334) — any sufficiently large negative additive term
  at any stage can already swallow an earlier positive contribution once the running score is near
  zero. The new §9b block follows this exact, pre-existing shape and placement (immediately after
  §9, before the final `dataclasses.replace`); it does not introduce a new or differently-ordered
  clamp risk relative to what §9 already does. This is existing formula design (scores are
  intentionally floored non-negative at each stage), not a defect this ticket's diff introduced —
  confirmed **fixture gap, not formula defect**.
- Fix: added `entity.lifecycle.dependent_entity_ids = []` to `_make_entity()` in
  `tests/unit/domains/faction/test_faction_directive_propagation.py`, matching real production's
  default-empty-list behavior for an entity with no dependents. This is a test-hygiene fix
  (completing the fixture's existing configure-every-read-attribute pattern for a newly-read
  field), not a change to `scoring.py` or a weakening of the test's assertion.

## Test Summary

- `tests/unit/domains/adventure/test_scoring_dependent_bias.py` (new, 4 tests) — all pass.
- `tests/unit/domains/adventure/` (full directory, 92 tests including the new file) — all pass, no
  regressions.
- `tests/unit/progression/test_lifecycle.py` (27 tests including 2 new) — all pass, no regressions.
- `tests/unit/progression/` + `tests/unit/domains/adventure/` + `tests/architecture/` combined
  (253 tests) — all pass.
- `tests/architecture/test_adventure_route_score_max_unchanged.py` — passes unmodified (Step 7
  verification), confirming `_ADVENTURE_ROUTE_SCORE_MAX` (2.9) and
  `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` (2.4) are untouched.
- Regression fix re-verification: `tests/unit/domains/faction/test_faction_directive_propagation.py`
  + `tests/unit/domains/adventure/test_scoring_dependent_bias.py` together — 12 passed.
- Full previously-scoped command re-run: `pytest tests/unit/core/ tests/unit/domains/
  tests/unit/progression/ tests/architecture/ tests/unit/social/
  tests/integration/optimization/ tests/unit/strategic/ tests/unit/ai/goals/ -q` — **1790 passed**,
  0 failed, no other regressions found.

## Files Changed

- `src/core/state.py` — `LifecycleComponent.dependent_entity_ids` field + `to_canonical_dict()`.
- `src/core/updates.py` — `LifecycleUpdate.dependent_entity_ids_add` field + `is_noop()`/`merge()`.
- `src/engine/patches.py` — `LifecyclePatch.apply()` extend-then-tuple-assign for the new field.
- `src/core/builder.py` — `V2EntityBuilder.lifecycle(dependent_entity_ids=...)` kwarg.
- `src/domains/adventure/schema.py` — `AdventureRouteOption.dependent_bias` trace field.
- `src/domains/adventure/scoring.py` — new §9b bias block in `AdventureRouteScorer.score()`.
- `tests/unit/domains/adventure/test_scoring_dependent_bias.py` — new test file (4 tests).
- `tests/unit/progression/test_lifecycle.py` — 2 new write-path tests appended.
- `docs/mechanics/04_strategic_cognition.md` — new §6.13 (SOC-262).
- `docs/mechanics/05_world_evolution.md` — new "Personal Dependents (Non-Parental)" subsection.
- `docs/core/entities.md` — Lifecycle component-table row updated.
- `docs/parity_ledger/social_narrative.yaml` — new `SOC-262` entry (via `write_entry()`).
- `tests/unit/domains/faction/test_faction_directive_propagation.py` — regression fix: `_make_entity()`
  now explicitly sets `entity.lifecycle.dependent_entity_ids = []`.
- `tickets/inprogress/TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS.md` — this ticket (Status,
  Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion
  Summary).
- `staging_artifacts/TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS/plan.md`,
  `staging_artifacts/TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS/investigation.md`,
  `staging_artifacts/TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS/test_plan.md` — pre-existing from
  this ticket's Scope/Plan phases; `plan.md` now carries a Deviations entry for the Test-phase
  regression fix described above.

## Completion Summary

Added a new durable `LifecycleComponent.dependent_entity_ids: list[int]` field with a full
`LifecycleUpdate`/`LifecyclePatch.apply()` write path mirroring the existing `heirlooms`
extend-then-tuple-assign pattern exactly, plus a `V2EntityBuilder.lifecycle()` construction kwarg
for tests/demo use. Added a new post-clamp §9b bias block to `AdventureRouteScorer.score()`
(`src/domains/adventure/scoring.py`) that reads `entity.lifecycle.dependent_entity_ids` directly
off the always-passed `entity` argument (never a new scorer parameter, avoiding the confirmed-dead
`faction_directives` pattern documented at §6.10): a `-2.0` penalty on `HUNT_WEAK_ENEMY` and a
`+1.0` bonus on `RECOVER`/`RETURN_TOWN` when an entity has at least one dependent, traced on a new
`AdventureRouteOption.dependent_bias` field. Covered with 4 new scoring tests and 2 new write-path
tests (all passing), documented in both `04_strategic_cognition.md` §6.13 and
`05_world_evolution.md`'s new Succession-adjacent subsection with explicit deferral of
birth-triggered parental auto-registration to the Reproduction epic, and recorded as parity ledger
entry `SOC-262` via the sanctioned `parity_ledger_writer.py` path. The pinned
`test_adventure_route_score_max_unchanged.py` architecture guard passes unmodified. The Test phase
surfaced one regression in an unrelated faction-directive test suite, root-caused to a
pre-existing shared `MagicMock(spec=EntityState)` fixture never anticipating the new
`entity.lifecycle.dependent_entity_ids` read (an unconfigured `MagicMock` attribute is
spuriously truthy, unlike real production's empty-list default) rather than any defect in
`scoring.py`'s clamp/floor ordering; fixed by explicitly configuring
`dependent_entity_ids = []` in that fixture. Full previously-scoped suite (1790 tests) now passes
with zero failures.
