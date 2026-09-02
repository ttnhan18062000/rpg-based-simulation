---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-ROLE-MODEL-IMITATION
artifact_type: plan
tags: [strategy, cognition]
---

# Implementation Plan — TCK-20260831-ROLE-MODEL-IMITATION

## Summary

Add a new `RoleModelBundle` sub-component (who an entity watches/admires, and how faithfully it
can imitate them) as the 6th field on `CognitionModel` (`src/core/cognition.py:524-530`), nested
under the already-live `EntityState.cognition` field exactly the way `RelationshipModel` is —
confirmed the correct target by investigation.md, not `SelfModelBundle`. A new authoritative pipeline
phase, `RoleModelSelectionPhase`, periodically (staggered per-entity cadence) scans nearby entities
via the existing `SpatialQueryService.nearby_entities`, picks the highest-`evolution_level` neighbor
as the admired role model, and stores an `intelligence_tier`-derived imitation-fidelity value
alongside it. The fidelity computation lives in a new sibling service,
`RoleModelImitationService` (`src/strategy/role_model_imitation.py`), which does **not** extend
`CapacityService.derive_profile` — a deliberate fork decision justified below. The phase follows the
exact same sequential-threading / read-through-then-replace shape `HabitBiasUpdatePhase`
(`src/domains/emotion/habit_phase.py:29-60`) already uses for `cognition_bundle_set`, which this
plan confirms (by reading `src/engine/pipeline.py`'s actual `run_phase` composition) makes the
`EntityUpdate.merge()` atomicity hazard investigation.md flagged a non-issue for this ticket's own
write pattern. Ships behind a new `ENABLE_ROLE_MODEL_IMITATION` flag, default `OFF`, per this
batch's established DEV-002 policy.

## Steps

### Step 1 — Add `RoleModelBundle` dataclass and nest it on `CognitionModel`
**Files:** `src/core/cognition.py`
**Change:** Following the exact pattern of `RelationshipModel` (`cognition.py:503-516`) and
`CognitionModel` (`cognition.py:523-544`, read in full — 5 existing sub-component fields:
`subjective`, `memory`, `motivation`, `commitment`, `relationships`), add:

```python
@dataclass(frozen=True, slots=True)
class RoleModelBundle:
    """Who this entity watches/admires as a role model, and how faithfully it can imitate them."""
    admired_entity_id: Optional[int] = None
    admired_since_tick: Optional[int] = None
    last_reconsidered_tick: Optional[int] = None
    imitation_fidelity: float = 0.5  # matches RoleModelImitationService.DEFAULT_FIDELITY (Step 3)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "admired_entity_id": self.admired_entity_id,
            "admired_since_tick": self.admired_since_tick,
            "last_reconsidered_tick": self.last_reconsidered_tick,
            "imitation_fidelity": round(self.imitation_fidelity, 4),
        }

    @classmethod
    def empty(cls) -> "RoleModelBundle":
        return cls()
```

Add `role_model: RoleModelBundle = field(default_factory=RoleModelBundle)` as a 6th field on
`CognitionModel`, and add `"role_model": self.role_model.to_canonical_dict()` to
`CognitionModel.to_canonical_dict()` (`cognition.py:532-539`). All fields are scalar
(`Optional[int]`/`float`) — no dict/set iteration, so determinism is automatic (no sorted-iteration
work needed, unlike `RelationshipModel.private_trust`).

**Lifecycle** (answers the ticket title's "choosing" framing): a single *current* role model at a
time (`admired_entity_id`), not a list/history — `admired_since_tick` marks when the current choice
started, `last_reconsidered_tick` marks the last time Step 5's phase re-evaluated the choice (even if
unchanged). Re-choosing simply replaces `admired_entity_id`/`admired_since_tick`; there is no
separate history log. This is the minimal lifecycle that satisfies "defined lifecycle (who is
watched/admired)" per AC #2 without over-building — a bounded history was considered per
investigation's `CommittedIntentionEntry` precedent note but rejected as scope creep for a ticket
rated "weakest implementability fit."

**Do NOT touch:** `SelfModelBundle` (`src/core/self_model.py`) — confirmed the wrong target by
investigation.md ("entirely self-directed... a role-model concept is inherently other-directed").
Do not add sorted-dict/set-iteration logic to `to_canonical_dict()` — all 4 fields are scalars, so
sorted iteration is unneeded machinery, unlike `RelationshipModel`/`PublicReputationProfile`'s
`Mapping` fields.
**Verify:** New test in Step 2.

### Step 2 — Schema/determinism tests for `RoleModelBundle`
**Files:** `tests/unit/entity/test_phase11_cognition_model_schema.py`
**Change:** Extend this file (established home for `CognitionModel` sub-component schema tests, per
investigation.md and the existing `test_entity_state_has_default_cognition_model` /
`test_cognition_model_serializes_deterministically` tests, lines 23-40 of that file) with:
- `test_entity_state_cognition_has_role_model_subcomponent` — default-construct `EntityState()`,
  assert `isinstance(entity.cognition.role_model, RoleModelBundle)` and that all 4 fields are at
  their safe defaults (`admired_entity_id is None`, `imitation_fidelity == 0.5`).
- `test_role_model_state_canonical_dict_deterministic` — two independently-constructed
  `CognitionModel()` instances (with `role_model` populated identically) produce `==`
  `to_canonical_dict()` output; assert `"role_model"` key is present in
  `CognitionModel().to_canonical_dict()`'s top-level output (shape-presence guard, mirroring
  `test_cognition_canonical_dict_shape_after_self_model_decision`, lines 48-50 of the same file).
- Re-run `test_subjective_model_has_no_self_field` and
  `test_cognition_canonical_dict_shape_after_self_model_decision` unmodified — regression guard
  that this addition did not reopen the `DEAD-COGNITION-SCHEMA-DECISION` cut.
**Do NOT touch:** `tests/unit/entity/test_phase2_self_model_components.py` — must keep passing
unmodified (proves the new state was not accidentally nested under `SelfModelBundle`).
**Verify:**
`pytest tests/unit/entity/test_phase11_cognition_model_schema.py tests/unit/entity/test_phase2_self_model_components.py -v`

### Step 3 — `RoleModelImitationService`: read `intelligence_tier`, compute imitation fidelity
**Files:** `src/strategy/role_model_imitation.py` (new file)
**Change:** Investigation.md's open design fork (fork (a): extend `CapacityService.derive_profile`;
fork (b): separate service) is resolved as **fork (b)** here — see justification below. New file,
sibling to `src/strategy/cognition_capacity.py` (co-located per the ticket's own Related Code Areas):

```python
class RoleModelImitationService:
    """Purely deterministic; does not mutate entity state.
    Resolves an entity's intelligence_tier-modulated imitation-fidelity multiplier.
    """
    HIGH_TIER_FIDELITY = 1.0
    LOW_TIER_FIDELITY = 0.5
    DEFAULT_FIDELITY = 0.5  # fallback when race/tier cannot be resolved

    @staticmethod
    def compute_imitation_fidelity(entity: "EntityState") -> float:
        race_id = entity.identity.properties.get("race_id")
        if not race_id:
            return RoleModelImitationService.DEFAULT_FIDELITY
        from src.content_semantics.faction import get_faction_semantics_service
        race_def = get_faction_semantics_service().repo.get_race(race_id)
        if race_def is None:
            return RoleModelImitationService.DEFAULT_FIDELITY
        tier = getattr(race_def, "intelligence_tier", None)
        if tier == "high":
            return RoleModelImitationService.HIGH_TIER_FIDELITY
        return RoleModelImitationService.LOW_TIER_FIDELITY
```

**Fork justification (design decision 3):** confirmed by reading `CapacityService.derive_profile`
in full (`src/strategy/cognition_capacity.py:14-56`) — it is a `@staticmethod`, pure function of
`entity.attributes`/`entity.identity.personality`/`entity.biological` only, with **zero**
content-catalog import today, and its docstring states "Purely deterministic; does not mutate entity
state" with no content-layer coupling (investigation.md). Adding a `CatalogRepository` dependency to
`derive_profile` would be the *first* content-catalog coupling in that function, for a concept
(imitation fidelity) unrelated to any of `CognitionProfile`'s existing 11 fields
(`max_active_projects`, `max_leads`, ..., `max_committed_intentions` — none imitation-related, per
investigation.md's full field list). A separate service avoids: (1) widening
`CapacityService.derive_profile`'s signature/dependencies for every existing caller, (2) conflating
`CognitionProfile` (attention/capacity limits) with imitation fidelity — the exact "four distinct
cognition concepts" conflation investigation.md's Anti-Drift Hazards section warns against.

**Read-path resolution (investigation.md confirmed live, cited here):**
`entity.identity.properties.get("race_id")` (`src/core/state.py:490`, `IdentityComponent.properties:
Dict[str, Any]`) → `CatalogRepository.get_race(def_id)` (`src/content/repository.py:435-436`) →
`RaceDefinition.intelligence_tier: str` (`src/content/schema.py:141`, `{"high","low"}`, landed by
`TCK-20260831-SPECIES-INTELLIGENCE-TIER`). Reuses the already-loaded `CatalogRepository` instance via
`get_faction_semantics_service().repo` (`src/content_semantics/faction.py:20-28,76-77` — confirmed
`self.repo` is a public attribute holding the same `CatalogRepository` that has `.get_race()`)
instead of instantiating a second `CatalogRepository`/adding a new `get_race_semantics_service()`
singleton — avoids a second catalog load, resolving investigation.md's open question on this point.
Reaching into the faction-named service for race data is a minor semantic mismatch but avoids
inventing a parallel singleton class for one field read on a "weakest implementability fit" ticket;
flagged, not hidden.

**Graceful degradation (AC #4's spirit, even though the dependency is landed — design decision 8):**
`race_id` absent (`.get("race_id")` returns `None`) or `CatalogRepository.get_race()` returning
`None` both fall through to `DEFAULT_FIDELITY` via `getattr(race_def, "intelligence_tier", None)`
and the `is None` checks above — never raises, matches this batch's established defensive-read
convention.
**Do NOT touch:** `CapacityService.derive_profile`'s existing signature or `CognitionProfile`'s
existing 11 fields (`src/core/strategic.py:363-378`). `RaceDefinition`/`intelligence_tier`'s own
definition (`src/content/schema.py`) — read-only consumption only.
**Verify:** New tests in Step 4.

### Step 4 — Tests for `RoleModelImitationService`
**Files:** `tests/unit/strategic/test_imitation_service.py` (new file, per test_plan.md's named
fork-(b) file choice)
**Change:**
- `test_imitation_scaling_reads_intelligence_tier_high_vs_low` — two entities built via
  `V2EntityBuilder` (`src/core/builder.py`, established pattern from
  `tests/unit/strategic/test_cognition_capacity.py`) differing only in `identity.properties["race_id"]`
  pointing at a `"high"`-tier vs `"low"`-tier race fixture; assert
  `compute_imitation_fidelity(high_entity) > compute_imitation_fidelity(low_entity)` and that the
  values equal `HIGH_TIER_FIDELITY`/`LOW_TIER_FIDELITY` exactly.
- `test_imitation_scaling_missing_race_or_tier_fails_safe` — entity with no `race_id` in
  `identity.properties`, and separately a `race_id` string that does not resolve via
  `CatalogRepository.get_race()`; both must return `DEFAULT_FIDELITY`, never raise.
- `test_capacity_service_signature_unchanged_by_role_model_fork` — regression guard (test_plan.md's
  "CapacityService.derive_profile signature/return-shape guard"):
  `{f.name for f in dataclasses.fields(CognitionProfile)}` equals the known 11-field set, proving
  Step 3's fork did not touch `CognitionProfile`.
**Do NOT touch:** `tests/unit/strategic/test_cognition_capacity.py` — must keep passing completely
unmodified (fork (b) means this file has zero required changes).
**Verify:** `pytest tests/unit/strategic/test_imitation_service.py tests/unit/strategic/test_cognition_capacity.py -v`

### Step 5 — `RoleModelSelectionPhase`: the watching/choosing logic
**Files:** `src/strategy/role_model_phase.py` (new file, co-located with Step 3's service under
`src/strategy/`, not a new `src/domains/cognition/` folder — no such folder exists today across
`src/domains/*` and inventing one is a bigger structural decision than this ticket should make
unilaterally)
**Change:**

```python
class RoleModelSelectionPhase:
    """Authoritative per-tick (cadence-gated) writer for role-model watching/choosing."""

    RADIUS = 10.0  # matches SpatialQueryService.nearby_entities call convention elsewhere
                   # (src/systems/strategic_systems/intelligence.py:144)

    @staticmethod
    def apply(state: "AuthoritativeState", update: "StateUpdate") -> "StateUpdate":
        from dataclasses import replace
        from src.core.updates import EntityUpdate
        from src.engine.cadence import should_run, SystemCadence
        from src.engine.spatial_query import SpatialQueryService
        from src.strategy.role_model_imitation import RoleModelImitationService

        cadence = SystemCadence().social_memory  # reuse existing tier, no new SystemCadence field
        entity_updates = dict(update.entity_updates)
        for entity_id, entity in state.entities.items():
            if not should_run(state.tick, entity_id, cadence):
                continue

            entity_update = entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
            base_cognition = (
                entity_update.cognition_bundle_set
                if entity_update.cognition_bundle_set is not None
                else entity.cognition
            )
            current = base_cognition.role_model

            nearby_ids = SpatialQueryService.nearby_entities(
                state, entity.navigation.position, radius=RoleModelSelectionPhase.RADIUS
            )
            best_id, best_level = None, entity.identity.evolution_level
            for nid in sorted(nearby_ids):  # deterministic tie-break: lowest entity_id
                if nid == entity_id:
                    continue
                other = state.entities.get(nid)
                if other is None:
                    continue
                if other.identity.evolution_level > best_level:
                    best_id, best_level = nid, other.identity.evolution_level

            # Validate existing choice still present in the world; else it's implicitly cleared
            # by the reselection below (best_id recomputation does not special-case "keep current
            # unless a strictly-better candidate exists" -- every cadence tick recomputes fresh).
            if best_id != current.admired_entity_id:
                new_role_model = replace(
                    current,
                    admired_entity_id=best_id,
                    admired_since_tick=state.tick,
                    last_reconsidered_tick=state.tick,
                    imitation_fidelity=RoleModelImitationService.compute_imitation_fidelity(entity),
                )
            else:
                new_role_model = replace(
                    current,
                    last_reconsidered_tick=state.tick,
                    imitation_fidelity=RoleModelImitationService.compute_imitation_fidelity(entity),
                )
            new_cognition = replace(base_cognition, role_model=new_role_model)
            entity_updates[entity_id] = replace(entity_update, cognition_bundle_set=new_cognition)

        return replace(update, entity_updates=entity_updates)
```

**Cadence (design decision 4):** reuses the existing `SystemCadence.social_memory` tier (10 ticks,
`src/engine/cadence.py:26`, "Strategic / Cognition (High Cost)" bucket) via the existing
`should_run(tick, entity_id, cadence)` per-entity-staggered helper
(`src/engine/cadence.py:38-52` — confirmed it staggers by `(tick + entity_id) % cadence == 0` to
avoid all-entities-same-tick spikes, and is already used this way at
`src/engine/domain/cognition.py:48-49`). Deliberately **not** `DemographicCycleService`'s 200-tick
`COHORT_INTERVAL` (`src/domains/demographics/cohort.py:334,351`) — that cadence is for a
region-level, world-scale process; role-model watching is a per-entity cognitive re-evaluation, the
same cost class as `strategic_intelligence`/`social_memory`, not a slow world-macro cycle. No new
`SystemCadence` field is added — reusing `social_memory` keeps this minimal, matching the ticket's
"weakest implementability fit" framing.

**Selection signal:** proximity via `SpatialQueryService.nearby_entities(state, pos, radius=10.0)`
(`src/engine/spatial_query.py:44+`, confirmed real, called with this exact signature at
`src/systems/strategic_systems/intelligence.py:144`) + `entity.identity.evolution_level`
(`src/core/state.py:477`, a real, existing "how accomplished is this entity" field — no new
attribute invented) as the admiration criterion: the nearest-by-proximity-radius neighbor with the
strictly highest `evolution_level` above the watcher's own becomes the admired entity. Deterministic
tie-break: iterate `sorted(nearby_ids)` so equal-`evolution_level` candidates resolve by lowest
`entity_id`, not dict/set iteration order.

**Merge-atomicity resolution (design decision 2 — answers investigation.md's flagged risk):** No
real risk for this ticket's write pattern. Confirmed by reading `src/engine/pipeline.py`'s actual
`refine()` composition (lines ~140-175): every existing `cognition_bundle_set`-producing phase today
(`MemoryUpdatePhase` at "memory_update", `HabitBiasUpdatePhase` at "habit_bias_action_style") is
wired via plain sequential threading —
`update = run_phase("<name>", update, lambda u: Phase.apply(state, u, ...), "<FLAG>")` — where each
phase receives the *already-updated* `update` from the previous phase and internally reads
`entity_updates.get(entity_id, ...)` fresh off that same object before replacing (the
read-through-then-replace idiom, `habit_phase.py:47-58`). This is categorically different from
`StateUpdate.merge()`/`EntityUpdate.merge()`, which is used elsewhere in `refine()`
(`u.merge(InformationBeliefPhase.apply(state, ...))` at `pipeline.py:188`, similarly at lines 227,
257, 267, 291) to fold in a *separately-built* `StateUpdate` computed straight off `state` rather
than off the threaded `update` — that is where investigation.md's last-write-wins hazard could
actually bite, but none of those `.merge()`-based phases (`InformationBeliefPhase`,
`FactionAwarenessService`, diplomatic tension, `MilitaryConflictPhase`, `CombatEngagementPhase`) set
`cognition_bundle_set` anywhere (confirmed: they only touch `strategic`/`intent_results`/
`property_updates`/`faction_updates`/`world_events_add`). This plan registers
`RoleModelSelectionPhase` the same sequential-threading way (Step 6) — never via `.merge()` for
`cognition_bundle_set` — so it participates in the existing safe convention rather than the risky
one. The general-purpose regression-locking test test_plan.md calls for (a targeted
`EntityUpdate.merge()` last-write-wins lock test) is still worth adding as a standing guard against
a *future* change accidentally routing a `cognition_bundle_set` producer through `.merge()`, but it
is not required by this ticket's own correctness.
**Do NOT touch:** `src/engine/apply.py`, `src/engine/patches.py`, `src/core/updates.py` — the
wholesale `cognition` passthrough (`apply.py:610-611`) requires zero changes for a new
`CognitionModel` sub-component, per investigation.md's confirmed trace.
**Verify:** New tests in Step 7.

### Step 6 — Register the phase in the pipeline behind a new feature flag
**Files:** `src/engine/pipeline.py`, `src/domains/optimization/feature_flags.py`
**Change:** In `feature_flags.py`'s `FeatureFlagManager._flags` dict (`feature_flags.py:13+`), add,
following the exact comment convention already used for `ENABLE_HABIT_BIAS_ACTION_STYLE` and
`ENABLE_CREATURE_TERRITORY_LIFECYCLE` (both landed this same session, `feature_flags.py:122-133`):

```python
# New gameplay behavior (TCK-20260831-ROLE-MODEL-IMITATION): wires RoleModelSelectionPhase into
# refine() for the first time -- per-entity proximity-based role-model watching/choosing plus
# intelligence_tier-modulated imitation fidelity. DEV-002 default-OFF policy applies -- brand-new
# mechanic, no corpus profile turns this on and no SHADOW-validation history exists.
"ENABLE_ROLE_MODEL_IMITATION": FeatureMode.OFF,
```

No new `docs/guidelines/intentional_divergences.md` entry needed — matches the precedent that
`ENABLE_MEMORY_UPDATE` (2.47), `ENABLE_HABIT_BIAS_ACTION_STYLE`, and
`ENABLE_CREATURE_TERRITORY_LIFECYCLE` each got only this inline comment citing DEV-002, not their
own new DEV-XXX entry, because DEV-002 already covers "new phase, default OFF" as a standing policy
(`docs/guidelines/intentional_divergences.md:1509-1517`). (Exception: `MemoryUpdatePhase` *also* got
divergence entry 2.47 because it changed action-routing scoring behavior, a substantive behavior
shift beyond "new phase exists" — this ticket has no equivalent existing behavior to diverge from,
so no entry is needed, matching the simpler `HABIT-BIAS-WIRING`/`CREATURE-TERRITORY-LIFECYCLE`
precedent instead.)

In `pipeline.py`, immediately after the existing `habit_bias_action_style` block
(`pipeline.py:160-173`, confirmed read in full) and before the `self_model` block, add:

```python
# --- Role Model Selection (TCK-20260831-ROLE-MODEL-IMITATION) ---
# Runs strictly after habit_bias_action_style so it reads through any same-tick
# cognition_bundle_set write that phase already staged (read-through-then-replace), independently
# gated by its own flag.
t_start = time.perf_counter_ns()
from src.strategy.role_model_phase import RoleModelSelectionPhase
update = run_phase(
    "role_model_selection", update,
    lambda u: RoleModelSelectionPhase.apply(state, u),
    "ENABLE_ROLE_MODEL_IMITATION",
)
costs["role_model_selection"] = (time.perf_counter_ns() - t_start) / 1e6
```

`PhaseDependencyGraph.PHASES` (`src/engine/phase_graph.py:36+`) registration is intentionally
**skipped** — confirmed `should_run_phase` returns `True` (always run) for any `phase_name not in
PHASES` (`phase_graph.py:82-83`), and `HabitBiasUpdatePhase`'s own `"habit_bias_action_style"` name
is likewise absent from that dict (only `"memory_update"` appears, `phase_graph.py:62`) — this
ticket follows the more recent precedent (omit registration) rather than inventing a new
`PhaseMetadata` entry, an optimization out of scope here.
**Do NOT touch:** the `memory_update` or `self_model` blocks' own logic — only insert a new block
between them.
**Verify:** New tests in Step 7 (unit) and Step 8 (integration wiring).

### Step 7 — Lifecycle/behavior tests for `RoleModelSelectionPhase`
**Files:** `tests/unit/strategic/test_role_model_state.py` (new file, per test_plan.md's named file)
**Change:**
- `test_role_model_lifecycle_add_and_clear` — construct a 2-entity `AuthoritativeState` (via the
  established `V2EntityBuilder` pattern) where one entity has a strictly higher `evolution_level`
  and is within `radius=10.0`; call `RoleModelSelectionPhase.apply()` at a tick satisfying
  `should_run`; assert the lower-level entity's resulting `cognition_bundle_set.role_model.admired_entity_id`
  equals the higher-level entity's id, and `admired_since_tick`/`last_reconsidered_tick` both equal
  the call tick.
- A second case where the previously-admired entity is removed from `state.entities` (or moved out
  of radius) between two calls: assert `admired_entity_id` becomes `None` on the next cadence tick
  (implicit clear via recomputation, not a special "clear" method — matches Step 5's design).
- A cadence-gating case: calling `apply()` at a non-`should_run` tick for a given entity produces no
  change to that entity's `role_model` (its `cognition_bundle_set` for that entity is either absent
  or, if present from another phase, its `role_model` sub-field is untouched).
- `test_role_model_selection_stores_imitation_fidelity` — asserts the resulting `role_model.imitation_fidelity`
  matches `RoleModelImitationService.compute_imitation_fidelity(entity)` for the same entity/tick —
  proves Step 5 and Step 3 are wired together, not just independently correct.
**Do NOT touch:** `tests/unit/strategic/test_committed_intention_model.py` — a secondary pattern
reference only (per investigation.md), not something this ticket modifies.
**Verify:** `pytest tests/unit/strategic/test_role_model_state.py -v`

### Step 8 — Integration test: apply-pipeline round trip includes the new sub-component
**Files:** `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`
**Change:** Add `test_cognition_bundle_set_apply_round_trip_includes_role_model` (test_plan.md's
named test): build an `EntityUpdate` with `cognition_bundle_set` carrying a `CognitionModel` whose
`role_model` sub-field is populated (`admired_entity_id` set to a real id, non-default
`imitation_fidelity`), drive it through `ApplyPath._apply_entity_update`/`apply_generation`
end-to-end (established pattern already used elsewhere in this file for the other 5
`CognitionModel` sub-components), and assert the resulting `EntityState.cognition.role_model` on the
reconstructed entity is present and unmodified. This is the concrete proof (not an assumption) that
nesting under `CognitionModel` needed zero `apply.py`/`patches.py` changes, per investigation.md's
trace.
Also run `ENABLE_ROLE_MODEL_IMITATION=OFF` (default) through one full-pipeline tick in this same
file/a sibling test to assert the flag defaults off and `RoleModelSelectionPhase` does not run
(mirrors `test_adventure_routing_defaults_off`-style sentinel precedent, DEV-002).
**Do NOT touch:** the existing 5 sub-component assertions already in this file for
`subjective`/`memory`/`motivation`/`commitment`/`relationships` — extend, do not rewrite.
**Verify:** `pytest tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py -v`

### Step 9 — Documentation: Mechanics Bible + parity ledger
**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`
**Change:** In `04_strategic_cognition.md`, add a new `### Role-Model Watching & Imitation Fidelity
(TCK-20260831-ROLE-MODEL-IMITATION)` subsection under §3/§4 (matching the established
`### <Title> (TCK-...)` pattern, e.g. `### Lead Contradiction Testing (E42D; ...)` at line 95). Cover
at a narrative level: `RoleModelBundle`'s 4 fields and their meaning; the per-entity staggered
`social_memory`-cadence (10-tick) re-evaluation; the proximity (`radius=10.0`) +
`evolution_level`-comparison selection rule; the `intelligence_tier → imitation_fidelity` mapping
(`"high"` → `1.0`, `"low"`/unresolved → `0.5`); and the `ENABLE_ROLE_MODEL_IMITATION` default-OFF
gate.

In `strategic_cognition.yaml`, add a new entry at the next free sequential id after the file's
current highest (`STRAT-263`, confirmed by scanning the full file — no gaps below that were
preferred over appending at the end):

```yaml
- id: STRAT-264
  text: 'RoleModelSelectionPhase periodically (per-entity staggered social_memory cadence)
    selects the nearest strictly-higher-evolution_level neighbor within radius=10.0 as an
    entity''s admired role model (CognitionModel.role_model), and stores an
    intelligence_tier-derived imitation_fidelity (RoleModelImitationService) alongside it --
    gated off by default behind ENABLE_ROLE_MODEL_IMITATION (DEV-002).'
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/strategy/role_model_phase.py (RoleModelSelectionPhase.apply); src/strategy/role_model_imitation.py
    (RoleModelImitationService.compute_imitation_fidelity); src/core/cognition.py (RoleModelBundle,
    CognitionModel.role_model).
  proof_type: regression
  test_path: tests/unit/strategic/test_role_model_state.py
```
**Do NOT touch:** any existing `STRAT-*` entry, `STRAT-208`–`STRAT-212` (cognition-profile capacity)
or `STRAT-122`–`STRAT-127` (intel-capacity) — nearest neighbors by subject only, not entries this
ticket modifies.
**Verify:** `python3 tools/validate_frontmatter.py` (if applicable to this file) and a manual read
confirming the YAML parses; no automated test covers doc prose directly.

## Scope Guards

- Do not extend `RelationshipRole` (`src/core/models/social.py`) with a new enum member — Out of
  Scope. The optional idea-22 pairing (visually surfacing the role-model relationship as `FRIEND` on
  an *existing* `SocialBond`) is explicitly **not** part of this plan's Steps — it is optional per
  the ticket text and is deferred entirely, not silently included.
- Do not modify `RaceDefinition`/`intelligence_tier`'s own definition or
  `data/content/living/races.yaml` — read-only consumption only (Steps 3-4).
- Do not touch `CapacityService.derive_profile`'s signature or `CognitionProfile`'s 11 existing
  fields (Step 3's fork decision).
- Do not touch `src/engine/apply.py`, `src/engine/patches.py`, `src/core/updates.py` — the
  wholesale `cognition` passthrough needs zero changes (Step 5).
- Do not add a new `SystemCadence` field — reuse `social_memory` (Step 5).
- Do not register a new `PhaseDependencyGraph.PHASES` entry — out of scope optimization (Step 6).
- Do not build any actual behavior-copying/imitation-learning mechanism — `imitation_fidelity` is
  the minimal real hook point AC #3 requires ("reads intelligence_tier to modulate behavior"), not a
  full feature.
- Do not add a new `docs/guidelines/intentional_divergences.md` entry — DEV-002 already covers this
  case (Step 6).

## Dependency Map

- Step 2 depends on Step 1 (tests the dataclass Step 1 adds).
- Step 4 depends on Step 3 (tests the service Step 3 adds).
- Step 5 depends on Steps 1 and 3 (uses `RoleModelBundle` and `RoleModelImitationService`).
- Step 6 depends on Step 5 (registers the phase Step 5 defines).
- Step 7 depends on Step 5 (and indirectly Step 6 is not required for Step 7's tests, which can call
  `RoleModelSelectionPhase.apply()` directly without going through the pipeline).
- Step 8 depends on Step 6 (tests the pipeline-registered flag/phase).
- Step 9 depends on Steps 1, 3, 5, 6 (documents the final field names/formula/flag name — written
  last so nothing drifts from what actually landed).
- Steps 1-4 are otherwise independent of each other in implementation order (1↔2 and 3↔4 could be
  done in either relative order, but 5 needs both 1 and 3 complete).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — related_tickets lists TCK-20260831-SPECIES-INTELLIGENCE-TIER as hard prerequisite | Already satisfied in the ticket document itself (`## Related Tickets` section, confirmed present) — no plan step required | Manual inspection of `tickets/inprogress/TCK-20260831-ROLE-MODEL-IMITATION.md`'s Related Tickets section (already true) |
| AC #2 — new typed role-model/imitation state on `EntityState`, defined lifecycle, round-trip tested | Steps 1, 2, 5, 7, 8 | `test_entity_state_cognition_has_role_model_subcomponent`, `test_role_model_state_canonical_dict_deterministic`, `test_role_model_lifecycle_add_and_clear`, `test_cognition_bundle_set_apply_round_trip_includes_role_model` |
| AC #3 — imitation-sophistication scaling reads `intelligence_tier` to modulate behavior | Steps 3, 4, 5, 7 | `test_imitation_scaling_reads_intelligence_tier_high_vs_low`, `test_role_model_selection_stores_imitation_fidelity` |
| AC #4 — stub/defer path if shipped before `intelligence_tier` lands, never silently coupled | Not exercised — dependency confirmed already landed (investigation.md, ticket Assumptions section). Step 3's `getattr`/`.get()` defensive-read pattern still guards against a malformed/missing race at runtime, satisfying the "never crash" spirit even though the stub branch itself is not built | `test_imitation_scaling_missing_race_or_tier_fails_safe` |

## Anti-Drift Notes

- Four distinct "cognition" concepts coexist in this codebase (investigation.md): `CognitionModel`
  (state schema, `src/core/cognition.py`), `SelfModelBundle` (`src/core/self_model.py`),
  `CognitionProfile` (derived by `CapacityService`, `src/core/strategic.py`), and
  `CognitionProfileDefinition` (content catalog, `src/content/schema.py`). This plan's new state
  goes in the first; the new scaling logic reads from `RaceDefinition.intelligence_tier` (a sibling
  field of, but distinct from, `CognitionProfileDefinition`/`cognition_profile`) — do not let
  implementation drift into touching the second or third.
- `RoleModelBundle.to_canonical_dict()` participates in the authoritative canonical hash
  unconditionally (`CanonicalStateHasher`, `src/engine/checkpoint.py:63`, per `SelfModelBundle`'s own
  docstring precedent) — all 4 fields are scalars so this is automatically deterministic, but if a
  future change adds a collection-typed field here, sorted iteration is required, matching every
  existing sibling sub-component.
- `RoleModelSelectionPhase` and `RoleModelImitationService` must both stay read-only on `state` —
  the only durable write is the `cognition_bundle_set` returned via the `StateUpdate`/`EntityUpdate`
  path, never a direct mutation, matching the project's Decision-logic-reads-state /
  Durable-changes-through-typed-updates rule.
- The `EntityUpdate.merge()` last-write-wins hazard investigation.md flagged is real *in general*
  (confirmed live at `src/core/updates.py:719`) but does not apply to this ticket's own write path
  because `RoleModelSelectionPhase` is registered via sequential `run_phase` threading, not
  `.merge()` — see Step 5's "Merge-atomicity resolution" for the full trace. Do not later refactor
  this phase's registration to use `u.merge(RoleModelSelectionPhase.apply(state, StateUpdate()))`
  style composition (building its update off bare `state` instead of the threaded `update`) — that
  would reopen the exact hazard this plan avoided.
- Idea 22 (`RelationshipRole`/`SocialBond.role`) stays fully unrelated code — do not let the
  "suggested pairing" language in the ticket's Scope section turn into an implicit requirement; it
  is optional and this plan deliberately does not include it as a step.

## Open Questions

All design decisions for this ticket are resolved in this plan — none are left open for
architecture-review or implementation-time judgment calls:
1. State shape/nesting: resolved (Step 1, `RoleModelBundle` under `CognitionModel`).
2. `EntityUpdate.merge()` atomicity risk: resolved as a non-issue for this ticket's write pattern
   (Step 5's "Merge-atomicity resolution").
3. `CapacityService` vs. separate-service fork: resolved as separate service (Step 3).
4. Selection-phase placement/cadence/signal: resolved (Step 5/6 — `social_memory` cadence,
   proximity + `evolution_level`, sequential registration after `habit_bias_action_style`).
5. Round-trip test shape: resolved (Steps 2, 7, 8).
6. Docs: resolved (Step 9, including the next free parity ledger id, `STRAT-264`).
7. Feature flag: resolved — ships behind `ENABLE_ROLE_MODEL_IMITATION`, default `OFF` (Step 6).
8. AC #4 fallback: resolved — moot in practice (dependency landed) but defensive `getattr`/`.get()`
   degradation is still implemented (Step 3).

## Deviations (recorded during Implement)

- **Step 8's "existing 5 sub-component assertions already in this file" premise did not hold.**
  `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` was read in full during
  implementation and contains exactly one pre-existing test
  (`test_cognition_hierarchy_e2e_smoke`), which constructs a `CognitionModel` directly via
  `replace()` and never drives it through `ApplyPath` at all — it is not five per-sub-component
  apply-path round-trip assertions as the plan's Step 8 text describes. This did not block the
  step: the two new tests (`test_cognition_bundle_set_apply_round_trip_includes_role_model`,
  `test_role_model_imitation_flag_defaults_off_and_phase_does_not_run`) were still added to this
  same file as directed, and the pre-existing smoke test was left untouched exactly as the "Do NOT
  touch" guard required. For the actual apply-path round-trip pattern, a dedicated research pass
  found the correct real analog to mirror is
  `tests/integration/optimization/test_component_patch_apply_parity.py::test_self_model_patch_apply_parity_durable_materialization`
  (drives a bundle through `ApplyPath.apply_generation()` end-to-end), not anything already living
  in `test_phase18_cognition_hierarchy_e2e.py` itself. No plan step's substance changed — only the
  "already in this file" framing was inaccurate.
