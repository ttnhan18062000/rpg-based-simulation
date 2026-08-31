---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260824-WIRE-ORPHANED-MECHANISMS
artifact_type: plan
tags: [social, cognition, progression]
---

# Implementation Plan — TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Summary

This ticket wires 4 orphaned mechanisms into real production call sites (InformationNeedDetector,
EmotionUpdateService, compute_elder_attribute_update, consequence_events) and deletes 2 confirmed
dead duplicates (EvolutionService, SabotageAction). ReputationUpdateService was split out to
TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING and is explicitly Out of Scope here. Every insertion
point and every field/type claim below was re-verified by direct file read during planning (not
inferred from investigation.md's prose alone) — three corrections to investigation.md's claims were
found and are called out explicitly in the affected steps: (1) `CognitionDomain.execute_brain()`'s
final line hardcodes `strategic=None`, which would silently discard the InformationNeedDetector
wiring unless changed; (2) `EmotionalModel` lives at `entity.cognition.subjective.emotion`, not
`entity.cognition.emotion` as investigation.md stated, requiring a nested two-level `replace()`;
(3) `evaluate_social_consequence()` returns `SimulationEvent` objects, not `WorldEvent` objects, so
the actual matching authoritative-observability sink is `CampaignOrchestrator._event_recorder.record()`
(already used by `_emit_domain_event()`/`_emit_chronicle_events()` in the same class), not the
`world_events_add`/`recent_world_events` (`WorldEvent`) pattern investigation.md's analogy to
`DemographicCycleService` implied. The two deletions were pre-checked for other writers via grep
(zero non-test, non-doc production references beyond each file's own definition) and the
ApplyPath/SabotageAction trauma-propagation dependency named in the task was verified generic
(keyed off `BuildingUpdate.hp_delta` reaching 0, not off `SabotageAction` the class) — no blocking
dependency found, so the delete proceeds without being flagged as unresolved.

## Steps

### Step 1 — Wire InformationNeedDetector into CognitionDomain.execute_brain()

**Files:** `src/engine/domain/cognition.py`

**Change:** In `CognitionDomain.execute_brain()` (`src/engine/domain/cognition.py:26-75`, confirmed
by direct read), insert a call to `InformationNeedDetector.detect_and_generate(entity, state.tick)`
(signature confirmed at `src/engine/domain/cognition_extras.py:47-50`: takes `entity`, `tick`,
returns `Optional[StrategicUpdate]`) between the existing "1. Emotional Appraisal" block (lines
61-67) and "2. Tactical Intent" block (line 70) — this is the ticket's Assumptions/Open Questions
RESOLVED decision, do not re-litigate placement.

**Critical correction to investigation.md**: the function's final line currently reads
`return {entity.id: replace(tactical_up, strategic=None, readiness_delta=0.0)}`
(`cognition.py:72-75`, confirmed by direct read) — it explicitly hardcodes `strategic=None`,
discarding whatever `TacticalDecisionSystem.evaluate_entity_intent()` may have set on
`tactical_up.strategic`. If the detector's result is computed but the final `replace()` call is left
unchanged, the wiring will silently no-op (the StrategicUpdate is computed but never reaches the
returned `EntityUpdate`). The final line must become:
`return {entity.id: replace(tactical_up, strategic=info_update, readiness_delta=0.0)}`
where `info_update = InformationNeedDetector.detect_and_generate(entity, state.tick)` (which is
`None` when no candidate exists — matching the field's existing `Optional[StrategicUpdate]` type,
confirmed at `src/core/updates.py:641`).

**Other writer to the same field (StrategicUpdate.projects_add_or_update)**:
`StrategicIntelligenceSystem.fused_strategic_pass()` (`src/systems/strategic_systems/intelligence.py:293`,
run later as pipeline phase `"strategic_intelligence"`, `src/engine/pipeline.py:354`) is the only
other production writer to `EntityUpdate.strategic` for the same entity in the same tick — per
`CognitionDomain`'s own class docstring (`cognition.py:16-18`) it is the sole owner of "Strategic
Planning (Authoritative)". Confirmed non-colliding: `fused_strategic_pass()` starts from
`refined_entity_updates = dict(update.entity_updates)` (`intelligence.py:305`, direct read) — the
same preserve-and-replace-specific-fields pattern used throughout this codebase's phases (matches
`LifecycleSystem.resolve_lifecycle()`, `NearDeathHardeningPhase.apply()`,
`MemoryUpdatePhase.apply()`), not a blind overwrite. `StrategicUpdate.merge()`
(`src/core/updates.py:543-583`, direct read) list-concatenates `projects_add_or_update` (line 560)
rather than replacing it, so even if `fused_strategic_pass()` merges its own `StrategicUpdate` onto
the entity's existing one, the INFORMATION_SEEKING project add from this step is additive, not
double-counted or clobbered. `execute_brain()` runs earlier in the tick (called from
`src/engine/executor.py:160`, before the `AuthoritativeApplyPipeline` phase sequence that includes
`strategic_intelligence`), so ordering is: detector fires first, `fused_strategic_pass()` composes
on top of it.

**Do NOT touch:** `TacticalDecisionSystem.evaluate_entity_intent()`, `AppraisalSystem`,
`StrategicIntelligenceSystem.fused_strategic_pass()`, `LeadRoutingSystem` — none of these need
edits; do not attempt to relocate the docstring's literal "after project eval, before route
scoring" wording into the pipeline-level systems (ticket's resolved decision keeps the call inside
`execute_brain()`).

**Required doc fix (added per architecture-review NEEDS_CHANGES finding — traceability/boundary
drift)**: `CognitionDomain`'s own class docstring (`cognition.py:16-18`) currently states, as System
Boundary #1, that "Strategic project and goal choice occurs exclusively inside the pipeline-level
`StrategicIntelligenceSystem.fused_strategic_pass()`." That boundary claim remains true in substance
after this step (arbitration/selection — `current_project_id_set` — still only ever comes from
`fused_strategic_pass()`; this step only *additively proposes* an `INFORMATION_SEEKING` candidate via
`StrategicUpdate.merge()`'s list-concatenation), but the docstring itself does not distinguish
"proposes candidates" from "selects/arbitrates," so it becomes misleading once this step lands. The
implementer must update `CognitionDomain`'s class docstring to add a boundary item, e.g.: "May
additionally propose `INFORMATION_SEEKING` project candidates via `InformationNeedDetector`
(non-authoritative — additive only); goal choice/arbitration remains exclusively
`fused_strategic_pass()`'s job." No behavior change, doc-only — keeps the class's self-declared
boundary honest instead of silently drifting from what the code now does.

**Verify:** `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` (extend) or new
`tests/integration/scenarios/test_information_seeking_wiring.py` —
`test_information_need_detector_fires_from_execute_brain`, a real Kernel/tick run (per AC #1's
explicit "verified via a real Kernel run" wording — a direct `execute_brain()` unit call alone does
not satisfy this AC). Regression: `tests/unit/cognition/`, `tests/unit/cognition/test_phase2_*.py`.

---

### Step 2 — Delete EvolutionService (dead duplicate)

**Files:** `src/progression/evolution.py` (delete)

**Change:** Delete `src/progression/evolution.py` in full. Pre-verified during planning (grep,
confirmed): `grep -rln "progression.evolution\|progression\.evolution" src/ tests/` returns zero
hits outside doc files (`docs/REGISTRY.yaml`, `docs/brainstorm/*.html`,
`docs/simulation/lifecycle_systems_contract.md`, `docs/archive/resource_v2/*.md`,
`docs/mechanics/attribute_progression_contract.md` — none are code imports); no `src/progression/__init__.py`
re-export exists. `EvolutionSystem` (`src/engine/evolution.py`) remains the sole live
goblin-evolution path, already pipeline-wired at `src/engine/pipeline.py:337`
(`run_phase("evolution", update, lambda u: EvolutionSystem.evaluate(state, u))`) and covered by
`tests/unit/progression/test_evolution.py::test_goblin_evolution`. No other writer touches this
file; it is inert code with zero callers and zero tests, so deletion has no downstream ripple.

**Do NOT touch:** `src/engine/evolution.py` (`EvolutionSystem`) — this is the live implementation,
not part of this deletion. Do not "reconcile" the 20-vs-25 threshold discrepancy into
`EvolutionSystem`; `EvolutionSystem`'s existing `[10, 25, 50]` thresholds are already the
parity-verified values (`docs/parity_ledger/progression.yaml` `PROG-001`/`PROG-026`/`PROG-034` etc.
cite only `src/engine/evolution.py`).

**Verify:** `tests/unit/progression/test_evolution.py` (existing tests must still pass unmodified —
proves `EvolutionSystem` remains the sole live path). Add a guard test (new, per test_plan.md item
2) asserting `src/progression/evolution.py` no longer exists / is never imported by
`src/engine/pipeline.py` or any phase file, in `tests/integrity/test_logic_guards.py` or extending
`tests/unit/progression/test_evolution.py`.

---

### Step 3 — Delete SabotageAction (dead duplicate), preceded by an ApplyPath trauma-propagation pre-check

**Files:** `src/town/sabotage.py` (delete); `tests/unit/world/test_building_sabotage.py` (update)

**Pre-check (already performed during planning — resolved, not blocking)**: verified whether the
trauma-propagation-on-building-destruction logic from TCK-20260425-PH7-M4-SABOTAGE is keyed off
`SabotageAction` specifically or off `BuildingUpdate`/building-destruction generically. Direct read
of `src/engine/apply_plan.py:194-218` (the actual location of this logic — NOT
`ApplyPath.apply_generation()` itself in `src/engine/apply.py`, which only calls
`ApplyPlanBuilder.build_plan()`; the building-mutation logic lives inside `ApplyPlanBuilder`, called
from there) shows:
```
for b_id, b_upd in update.building_updates.items():
    ...
    is_death = bld.functional and new_hp == 0
    new_buildings[b_id] = replace(bld, hp=new_hp, functional=False if new_hp == 0 else new_func, ...)
    if is_death:
        ...
        plan.world_collection_changes["regions"][region.id] = replace(current_r, trauma_score=current_r.trauma_score + 2.0)
```
This iterates generically over `update.building_updates` (a dict of `BuildingUpdate` objects) and
fires trauma propagation whenever a building's `functional` flag transitions True→False at
`new_hp == 0` — it reads no class/module identity, only the `BuildingUpdate` data shape. Both
`SabotageAction.apply()` and `BuildingSabotageSystem.resolve()` already emit plain `BuildingUpdate`
objects with `hp_delta`/`functional_set` (confirmed in investigation.md's direct reads of both
files). **Conclusion: no blocking dependency — trauma propagation is generic to `BuildingUpdate`,
not tied to `SabotageAction`. Proceeding with deletion; not flagged as unresolved.**

**Change:** Delete `src/town/sabotage.py` in full. `BuildingSabotageSystem` (`src/engine/sabotage.py`)
remains the sole live building-damage path, wired at `src/engine/pipeline.py:290`
(`run_phase("building_sabotage", ...)`), integration-tested by
`tests/integration/pipeline/test_strategic_cadence.py` and `tests/integrity/test_logic_guards.py`.
Update `tests/unit/world/test_building_sabotage.py` — its 3 existing tests
(`test_building_sabotage_damage`, `test_building_destruction_and_trauma`,
`test_sabotage_proximity_validation`) call `SabotageAction.apply()` directly and must be
removed/retargeted to `BuildingSabotageSystem.resolve()` as part of this same step, not left
silently failing (per test_plan.md item 3 and CLAUDE.md's "do not leave changes untested").

**Do NOT touch:** `src/engine/sabotage.py` (`BuildingSabotageSystem`) — do not fold
`SabotageAction`'s ATK-scaled damage formula into it; the flat-50 damage is the live, tested
behavior and changing it is out of this ticket's scope (a duplicate-check/delete ticket, not a
damage-formula redesign). Do not attempt to fix `BuildingSabotageSystem`'s own separate gap (no
production `SABOTAGE` work_kind intent generator exists — flagged in investigation.md as a distinct,
out-of-scope reachability gap).

**Verify:** `tests/unit/world/test_building_sabotage.py` (updated to target
`BuildingSabotageSystem`), `tests/integration/pipeline/test_strategic_cadence.py`,
`tests/integrity/test_logic_guards.py`. Add a guard test (per test_plan.md item 3) in
`tests/integrity/test_logic_guards.py` asserting building HP reduction traces to exactly one
authoritative source in the pipeline.

---

### Step 4 — Wire EmotionUpdateService into NearDeathHardeningPhase.apply()

**Files:** `src/engine/pipeline_phases/hardening.py`

**Change:** In `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py:18-95`,
confirmed by direct read), inside the existing `if not survived: continue` / near-death-threshold
block (after line 74's threshold check, alongside the existing `hardened_combat = combat_update.merge(...)`
construction at lines 76-85), add a call to
`EmotionUpdateService.update_on_event(entity.cognition.subjective.emotion, "near_death")`.

**Critical correction to investigation.md**: investigation.md states the access path as
`entity.cognition.emotion` — this is wrong. Direct read of `src/core/cognition.py:546-561`
(`CognitionModel`) confirms its fields are `subjective`, `memory`, `motivation`, `commitment`,
`relationships` — there is no `emotion` field on `CognitionModel` directly. `EmotionalModel` is
nested one level deeper, on `SubjectiveModel.emotion` (`src/core/cognition.py:218`,
`emotion: EmotionalModel = field(default_factory=EmotionalModel)`). The correct read/write path is
`entity.cognition.subjective.emotion`. Since `EntityUpdate.cognition_bundle_set` is a whole-`CognitionModel`
replace (`src/core/updates.py:655`), the wiring must build a **nested** two-level `replace()`:
```
updated_emotion = EmotionUpdateService.update_on_event(entity.cognition.subjective.emotion, "near_death")
new_subjective = replace(entity.cognition.subjective, emotion=updated_emotion)
new_cognition = replace(entity.cognition, subjective=new_subjective)
```
then set `entity_update.cognition_bundle_set = new_cognition` on the same `entity_update` this
method already builds via `replace(entity_update, combat=hardened_combat, cognition_bundle_set=new_cognition)`
(merging into the existing `refined_entity_updates[entity_id] = replace(entity_update, combat=hardened_combat)`
block at lines 87-90) — do not overwrite `combat=hardened_combat` in the same `replace()` call,
both must be set together. `EmotionUpdateService.update_on_event()`'s signature/behavior confirmed
by direct read (`src/domains/emotion/emotion_service.py:15-51`): pure function, `event_kind="near_death"`
branch increases `fear`/`panic`, decreases `confidence` (lines 24-27).

**Precedent followed**: `MemoryUpdatePhase.apply()` (`src/domains/memory/phase.py:48-53`, confirmed
by direct read) is the working precedent for `cognition_bundle_set` — it does
`replace(entity_up, cognition_bundle_set=new_entity.cognition)` after computing a fully-updated
`CognitionModel`, confirming this is the only architecturally sound path from a decision-layer
service back into durable `entity.cognition` state (no per-field `emotion_set` update type exists).

**Other writer to `EntityUpdate.cognition_bundle_set` for the same entity**: `MemoryUpdatePhase.apply()`
(pipeline phase "self_model"/"information_belief" area, runs earlier per `pipeline.py` ordering)
also writes `cognition_bundle_set`. `EntityUpdate.merge()` (`src/core/updates.py:714`,
`if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] = other.cognition_bundle_set`)
does **not** merge nested fields — it is a last-writer-wins overwrite of the whole bundle. Since
`NearDeathHardeningPhase` runs at pipeline phase `"near_death_hardening"`
(`src/engine/pipeline.py:357`), which is later than `"self_model"`/`"information_belief"`
(`pipeline.py:164,173`), if `MemoryUpdatePhase` already set `cognition_bundle_set` for the same
entity earlier in the same tick, this step's `new_cognition = replace(entity.cognition, ...)` MUST
read from the already-updated `entity_update.cognition_bundle_set` (if present on the entity_update
being processed in this phase) rather than from the stale `entity.cognition` (the pre-tick prior
state) — otherwise this step would silently discard `MemoryUpdatePhase`'s same-tick changes. Concretely:
`base_cognition = entity_update.cognition_bundle_set if entity_update.cognition_bundle_set is not None else entity.cognition`,
then build `new_subjective`/`new_cognition` from `base_cognition`, not unconditionally from
`entity.cognition`. This is a genuine same-tick collision the implementer must handle; the
determinism/integration test in Verify below must include a case where both phases fire in the
same tick for the same entity to prove no clobbering.

**Do NOT touch:** `AppraisalSystem.evaluate_emotional_state()` (`src/engine/cognition.py:76`) — this
is the unrelated, already-wired per-tick tactical appraisal; do not conflate or merge it with
`EmotionUpdateService`. Do not wire any of the other 5 `event_kind` strings
(`easy_win`/`repeated_failure`/`new_unknown`/`successful_goal`/`stagnation`) — no confirmed real
detection site exists for them (per ticket's RESOLVED Assumptions note); fabricating a trigger for
them is out of scope.

**Verify:** New test, `tests/unit/engine/test_near_death_hardening_emotion.py` (no existing
near-death-specific test file found) or extend
`tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` —
`test_near_death_hardening_updates_emotional_model`: proves a near-death survival produces an
`EntityUpdate.cognition_bundle_set` whose `.subjective.emotion` has `fear`/`panic` increased and
`confidence` decreased, and that `combat=hardened_combat`'s `max_hp_delta=5` from the existing logic
is preserved alongside it (both fields set together, neither dropped). Plus a
`cognition_bundle_set`-shape guard (per test_plan.md) proving only `.subjective.emotion` changed
relative to the entity's prior `CognitionModel` — no other sub-field (self-model, knowledge,
commitments) is clobbered by the whole-bundle replace. Regression:
`tests/unit/domains/emotion/test_phase16_emotion_update_service.py` (pure function, unchanged).

---

### Step 5 — Wire compute_elder_attribute_update into LifecycleSystem.resolve_lifecycle(), gated on forward bracket-entry transition

**Files:** `src/systems/lifecycle_systems/lifecycle.py`

**Change:** In `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py:36-60`,
confirmed by direct read), inside the existing life-stage transition block (lines 51-60), when
`target_stage == LifeStage.ELDER` (i.e., the same `is_forward_transition(entity.identity.life_stage, target_stage)`
edge already computed at line 56 — reused, not recomputed separately), additionally call
`compute_elder_attribute_update(e_id, entity.attributes, entity.lifecycle.age_ticks)`
(`src/domains/demographics/cohort.py:68-106`, confirmed by direct read: returns `None` for
`age_ticks < 7000` via `get_age_bracket(age_ticks) != "elder"` check at line 95, else an
`EntityUpdate(entity_id=..., attributes=AttributeUpdate(...))`). If non-`None`, merge its
`.attributes` field onto `ent_upd` via `ent_upd = ent_upd.merge(elder_update)`
(`EntityUpdate.merge()` confirmed at `src/core/updates.py:682-714`, `attributes` field merges via
`AttributeUpdate.merge()` — safe even if `ent_upd.attributes` is already non-`None` from another
source in the same tick).

**Why this satisfies the cadence-gating requirement**: reusing
`is_forward_transition(entity.identity.life_stage, target_stage)` (already gating the parallel
`life_stage_set` write at line 56, `src/ai/life_stage.py:59-66` confirmed by direct read: `True`
only if `target` has strictly higher ordinal than `current`) means the elder-attribute delta fires
on the exact same tick `life_stage` flips `ADULT → ELDER`, and never again afterward (monotonic
forward-only, `life_stage` stays `ELDER` on every subsequent tick, so `is_forward_transition()`
returns `False` thereafter) — this is the once-per-transition guard the investigation's Risk 3
demanded, achieved by piggybacking on the existing guard rather than inventing a new one.
`get_age_bracket()`'s "elder" string boundary (7000) and `LifeStage.ELDER`'s boundary (also 7000,
`src/ai/life_stage.py:54`) are intentionally duplicated but numerically identical (confirmed by
direct read of both), so gating the string-bracket-based function on the enum-based transition edge
is safe.

**Do NOT touch:** `get_age_bracket()`/`LifeStageService.get_stage_for_age()`'s intentional
duplication (`src/ai/life_stage.py:44-50` comment citing TCK-20260824-LIFE-STAGE-TRANSITIONS) — do
not consolidate the two vocabularies as part of this wiring.

**Verify:** `tests/unit/world/test_demographics.py` (existing `compute_elder_attribute_update`
tests must keep passing unmodified) plus two new tests (per test_plan.md item 6):
`test_elder_attribute_modifier_applies_once_on_bracket_transition` (entity crossing `age_ticks >=
7000` for the first time receives the deltas exactly once via `resolve_lifecycle()`) and
`test_elder_attribute_modifier_does_not_reapply_every_tick` (an already-elder entity does NOT
receive the deltas again on a subsequent tick — the concrete regression this step exists to
prevent). Update `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-DEMO-004` entry per Step 7.

---

### Step 6 — Wire consequence_events.evaluate_social_consequence() into CampaignOrchestrator._build_initial_state()

**Files:** `src/domains/campaigns/orchestrator.py`

**Change:** In `CampaignOrchestrator._build_initial_state()` (`src/domains/campaigns/orchestrator.py:575-710`,
confirmed by direct read), after the `entities: Dict[int, EntityState] = {}` reconstruction loop
(lines 605-646) and before the final `return AuthoritativeState(tick=0, seed=episode_seed,
entities=entities)` (line 710), add a loop over `sorted(entities.keys())` — **required per
architecture-review NEEDS_CHANGES finding**: use explicit `for eid in sorted(entities.keys()): entity
= entities[eid]` rather than plain `entities.items()`, matching this codebase's established
deterministic-iteration convention for exactly this kind of per-entity authoritative/observability
loop (`NearDeathHardeningPhase.apply()`'s `for entity_id in sorted(refined_entity_updates.keys())`,
and `docs/mechanics/04_strategic_cognition.md`'s documented "scanning ... in deterministic sorted
order every tick" pattern) — do not rely on unverified dict-insertion-order stability for
replay-determinism-relevant emitted-event ordering. Then for each entity call
`evaluate_social_consequence(entity, faction_id, self._state, tick=0)`
(`src/systems/social_systems/consequence_events.py:61-66`, confirmed signature by direct read:
`(entity, faction_id: str, campaign_state, tick: int = 0) -> List[SimulationEvent]`), where
`faction_id = f"faction_{entity.identity.faction}"` — this exact string convention
(`f"faction_{fac_int}"`) is already used elsewhere in the same class
(`_extract_faction_carry_forwards()`, `orchestrator.py:490`, confirmed by direct read) for deriving
a `faction_id` string from `entity.identity.faction` (`int`, default 0, `src/core/state.py:474`).
Note `EntityCarryForward` (`src/domains/campaigns/state.py:92-109`, confirmed by direct read) has
no `faction` field, so every reconstructed entity in `_build_initial_state()` keeps
`identity.faction`'s `EntityState` default (0) — this is pre-existing behavior, not something this
step changes or needs to fix.

**Critical correction to investigation.md's suggested pattern**: investigation.md says to emit
returned events "via the `world_events_add` authoritative-observability pattern... mirroring
`DemographicCycleService.process_demographics()`." Direct read shows this does not actually fit:
`evaluate_social_consequence()` returns `List[SimulationEvent]` (`src/observability/events.py`,
confirmed import at `consequence_events.py:35`), while `StateUpdate.world_events_add` /
`AuthoritativeState.recent_world_events` (the field `DemographicCycleService` populates) are typed
`List["WorldEvent"]` (`src/domains/world_emergence/schema.py`, confirmed at
`src/core/updates.py:931` and `src/core/state.py:1151`) — a different event type. Additionally,
`_build_initial_state()` constructs `AuthoritativeState` directly via its constructor; it does not
go through `StateUpdate`/`ApplyPath.apply_generation()` at all, so there is no `world_events_add`
merge step available at this call site regardless of type. The actual established sink for
`SimulationEvent` objects already exists on this same class: `CampaignOrchestrator._emit_domain_event()`
(`orchestrator.py:403-428`, confirmed by direct read) calls `self._event_recorder.record(SimulationEvent(...))`,
guarded by `if self._event_recorder is None: return` (mirrored at line 386 in `_emit_chronicle_events()`).
Since `evaluate_social_consequence()` already returns fully-typed `SimulationEvent` objects (not a
raw payload dict), the correct call is direct: `if self._event_recorder is not None:` then
`self._event_recorder.record(event)` for each returned event — no need to route through
`_emit_domain_event()`'s dict-wrapping (that helper exists for constructing a `SimulationEvent` from
scratch, which is not needed here since one is already returned).

**Do NOT touch:** `_get_spawn_entities()`, `_get_spawn_factions()`, `_extract_entity_carry_forwards()`,
`_extract_faction_carry_forwards()` — read-only reuse of the `faction_id` string convention from the
latter, no edits to any of these methods. Do not mutate `self._state` (`CampaignState`) or the
newly-built `entities` dict from within this loop — `evaluate_social_consequence()` is read-only by
contract (module docstring, `consequence_events.py:16-21`) and this step must remain read-only too,
only emitting via `self._event_recorder.record()`.

**Verify:** `tests/integration/scenarios/test_social_memory.py` (extend) —
`test_consequence_events_fire_at_episode_entity_spawn`: proves `evaluate_social_consequence()` is
called per spawned entity in `_build_initial_state()`, returned events reach
`self._event_recorder.record()` (not silently dropped when a recorder is injected), the function
call itself does not mutate `campaign_state`/`entities`, and the no-op path (no `_event_recorder`
injected) does not raise. Regression: `tests/unit/social/`.

---

### Step 7 — Docs and parity ledger alignment

**Files:** `docs/parity_ledger/world_dynamics.yaml`, `docs/parity_ledger/strategic_cognition.yaml`,
`docs/mechanics/01_entity_anatomy.md`, `docs/parity_ledger/social_narrative.yaml` (new entry),
possibly a new file or existing commitment/emotion-adjacent file for `EmotionUpdateService`
(no existing parity ledger entry anywhere references it — confirmed by investigation.md's grep).

**Change:**
- `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-DEMO-004` entry (lines 1143-1153): update
  `v2_evidence` to cite the real call site (`src/systems/lifecycle_systems/lifecycle.py`,
  `LifecycleSystem.resolve_lifecycle()`) alongside the existing `cohort.py` citation, and update
  `test_path` to include the new Step 5 integration test once written.
- `docs/mechanics/01_entity_anatomy.md` § "Biological Laws (Decay & Needs)" or "Progression &
  Growth": add the elder attribute-modifier formula (STR/AGI −30%, VIT/END −50%, WIS/CHA +30%,
  matching `compute_elder_attribute_update()`'s docstring exactly, `cohort.py:79-91`) — currently
  zero mentions of "elder" anywhere in this file despite `WORLD-DEMO-004` treating it as
  Mechanics-Bible-grounded.
- `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-229` entry (lines 2588-2602): update
  `v2_evidence`/`test_path` to cite the real `CognitionDomain.execute_brain()` call site and the
  Kernel-run-backed test from Step 1.
- New parity ledger entry for `EmotionUpdateService.update_on_event()` (near_death wiring only) —
  add to `docs/parity_ledger/social_narrative.yaml` (nearest existing subsystem file covering
  emotion/commitment-adjacent behavior per the Authoritative Mechanics Rule's "if no entry exists,
  add one"), citing `src/domains/emotion/emotion_service.py` +
  `src/engine/pipeline_phases/hardening.py` as `v2_evidence` and the Step 4 test as `test_path`.
- `docs/parity_ledger/social_narrative.yaml`'s `SOC-CROSS-EP-005` entry: update status/evidence to
  reflect the now-wired call site (`CampaignOrchestrator._build_initial_state()`) alongside the
  existing pure-function evidence, since it previously only verified the isolated function.

**Do NOT touch:** `docs/parity_ledger/progression.yaml` (no entries cite `EvolutionService`, nothing
to update for the Step 2 deletion — confirmed by investigation.md), `docs/simulation/domains/emotion_contract.md`
and `docs/simulation/domains/commitment_contract.md` (already describe accurate target-state
language per investigation.md, no textual correction required), any `ReputationUpdateService`-related
parity entry (does not exist; owned by the child ticket).

**Verify:** No test — this is a documentation/traceability step. `done-checker`'s
`frontmatter_valid` condition and the Authoritative Mechanics Rule's "if logic changes, update the
corresponding doc AND parity ledger entry in the same session" are the acceptance bar.

## Scope Guards

- Do not touch `ReputationUpdateService` (`src/domains/commitment/reputation.py`) or
  `src/domains/commitment/__init__.py`'s re-export of it — split to
  TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING.
- Do not touch `ReputationService` (`src/systems/social_systems/reputation.py`) — separately
  orphaned, not in this ticket's scope, thematically adjacent only.
- Do not touch `CooperationLearningService` (`src/domains/cooperation/services.py`) or
  `CooperationPhase` (`src/domains/cooperation/phase.py`) — dead code discovered during
  investigation, not in scope.
- Do not add `QuestKind.ESCORT` or any new `QuestKind` — out of scope, belongs to the child
  reputation ticket if ever pursued there.
- Do not "fix" the intentional `get_age_bracket()`/`LifeStageService.get_stage_for_age()`
  duplication — deliberate per `TCK-20260824-LIFE-STAGE-TRANSITIONS`.
- Do not touch `MemoryUpdatePhase` wiring or route-scoring logic — owned by
  TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING (C11).
- Do not touch `GeneticsSystem` — owned by M3 Reproduction.
- Do not fold `SabotageAction`'s ATK-scaled damage formula into `BuildingSabotageSystem` — out of
  scope beyond the duplicate-check/delete decision already made.
- Do not attempt to give `BuildingSabotageSystem` a production intent-generation trigger (it is
  itself currently unreachable from any AI decision path) — a separate, out-of-scope gap noted in
  investigation.md's Anti-Drift Hazards.
- Do not wire any `EmotionUpdateService` event_kind other than `"near_death"` — no confirmed
  detection site exists for the other 5.
- Do not use a direct/ad-hoc mutation path for `entity.cognition` anywhere in Steps 4/5/6 —
  `cognition_bundle_set` (Step 4) and `AttributeUpdate` merge (Step 5) are the only sanctioned
  typed paths; Step 6 is read-only and must not mutate state at all.

## Dependency Map

- Steps 1, 2, 3, 4, 5, 6 are independent of each other — different files, different subsystems, no
  shared call sites. They may be implemented and verified in any order or in parallel.
- Step 3's deletion depends on its own pre-check sub-step (already resolved above, not blocking) —
  no cross-step dependency remains.
- Step 7 (docs/parity) depends on Steps 1, 4, 5, 6 having landed (needs their real call-site
  citations and test paths) and on Step 2's confirmation that no `progression.yaml` entries need
  changes — sequence Step 7 last.
- No step depends on the split-out `ReputationUpdateService` ticket.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| InformationNeedDetector.detect_and_generate() is called from CognitionDomain.execute_brain() at the documented insertion point, verified via a real Kernel run | Step 1 | `test_information_need_detector_fires_from_execute_brain` (integration, real Kernel/tick run) |
| SabotageAction is either wired with a distinct purpose from the live BuildingSabotageSystem, or deleted/merged as a confirmed duplicate, with the duplicate check documented | Step 3 | Updated `tests/unit/world/test_building_sabotage.py`, `tests/integrity/test_logic_guards.py` guard test |
| EvolutionService wiring is preceded by an explicit duplicate-check against the live EvolutionSystem, proving additive or fold/delete | Step 2 | `tests/unit/progression/test_evolution.py`, new guard test in `tests/integrity/test_logic_guards.py` |
| EmotionUpdateService.update_on_event() is called from a real event-emission site, distinct from AppraisalSystem.evaluate_emotional_state() | Step 4 | `test_near_death_hardening_updates_emotional_model` |
| compute_elder_attribute_update() is called once per aging-cycle tick at the real aging-cycle call site (LifecycleSystem.resolve_lifecycle()) | Step 5 | `test_elder_attribute_modifier_applies_once_on_bracket_transition`, `test_elder_attribute_modifier_does_not_reapply_every_tick` |
| consequence_events.py's function is called at a real social/episode encounter entry point, read-only, emitted via the authoritative pipeline | Step 6 | `test_consequence_events_fire_at_episode_entity_spawn` |
| ~~ReputationUpdateService...~~ (split out) | N/A — not in this ticket | N/A |

## Anti-Drift Notes

- **Step 1**: the `strategic=None` hardcode in `execute_brain()`'s return line is the single most
  likely silent-failure point — an implementer who inserts the detector call but doesn't touch the
  final `replace()` line will produce code that "looks wired" (the call happens) but never actually
  affects the returned `EntityUpdate`. The Kernel-run integration test is the only thing that would
  catch this; a unit test calling `detect_and_generate()` directly would not.
- **Step 3**: do not skip the ApplyPath pre-check reasoning even though it resolved cleanly — if a
  future SabotageAction-adjacent change is proposed later, the generic `BuildingUpdate`-keyed trauma
  logic at `apply_plan.py:194-218` is the reference to re-check against, not this ticket's
  conclusion by itself.
- **Step 4**: the same-tick `cognition_bundle_set` collision with `MemoryUpdatePhase` (both write
  the whole bundle, last-writer-wins on `EntityUpdate.merge()`) is a real hazard specific to this
  wiring — `NearDeathHardeningPhase` must read from `entity_update.cognition_bundle_set` if already
  set earlier in the same tick, not from the stale pre-tick `entity.cognition`, or it will silently
  revert `MemoryUpdatePhase`'s same-tick changes to unrelated cognition sub-fields (self-model,
  knowledge, commitments, memory).
- **Step 5**: `compute_elder_attribute_update()` returns *delta* modifiers, not idempotent set
  values — reusing `is_forward_transition()`'s edge (rather than a fresh `age_ticks >= 7000` check
  every tick) is the only correct gate; a fresh unconditional check would compound the deltas every
  tick and drive elder attributes toward zero within a handful of ticks (investigation Risk 3).
- **Step 6**: `evaluate_social_consequence()` returns `SimulationEvent`, not `WorldEvent` — do not
  attempt to route these through `StateUpdate.world_events_add`/`recent_world_events`; the type
  mismatch would either fail typing/serialization or silently misfile the events into the wrong
  observability stream. Use `self._event_recorder.record()` directly.
- **Steps 2/3 (deletions)**: both pre-verified as zero-caller in `src/`/`tests/` (grep re-run during
  planning, not just trusted from investigation.md) — if a future rebase reintroduces a caller
  before this ticket lands, re-run the grep before deleting.

## Deviations (recorded during Implement)

- **Step 7 — parity ledger writer tool applies only to 2 of 4 edits.**
  `tools/parity_ledger_writer.py`'s `validate_entry()` enforces `schema.json`'s id pattern
  `^[A-Z]+-[0-9]{3}$` (single hyphen, letters then 3 digits) on every write, including an update to
  an already-existing entry. Two of the four entries this step touches have legacy multi-hyphen ids
  that predate this pattern's enforcement (`WORLD-DEMO-004`, `SOC-CROSS-EP-005` — both fail the
  pattern: `WORLD-DEMO-004` has 2 hyphens, `SOC-CROSS-EP-005` has 3). Calling `write_entry()` on
  either raises `EntryValidationError` on the id field alone, unrelated to any actual content change.
  Disposition: used `tools/parity_ledger_writer.py`'s `write_entry()` for the two conforming ids
  (`STRAT-229`, and the new `EmotionUpdateService` entry — assigned `SOC-248`, a fresh conforming id
  rather than a `SOC-EMO-*`-style compound one, specifically so it *can* go through the sanctioned
  writer); made small surgical direct edits via Edit for the two non-conforming legacy ids
  (`WORLD-DEMO-004`, `SOC-CROSS-EP-005`), then ran `python3 tools/parity_index.py build` by hand
  afterward to rebuild the derived index (the writer would have done this in-process automatically).
  Did not rename either legacy id to conform — that is a separate, unrelated cleanup outside this
  ticket's scope and would break any other doc/ledger cross-reference to those ids.
- **Step 1 test — Kernel-run tick count.** `ENTITY_BRAIN` work-item scheduling
  (`src/engine/scheduler.py`) is cadence-gated by `SystemCadence.strategic_intelligence`, and the
  *effective* cadence used is `GovernorPolicy`-mode-dependent (10 ticks NORMAL, 20 CONSTRAINED, 50
  DEGRADED, 100 SURVIVAL — `src/engine/policy.py`), not the plain `SystemCadence()` default of 10
  that `CognitionDomain.execute_brain()` itself references internally for its *own* idle/early-exit
  check. Under the minimal `RuntimeProfile` used by this kind of guard test (matching
  `tests/integrity/test_logic_guards.py`'s `integrity_profile` fixture pattern), the governor
  escalates to `DEGRADED` (cadence 50) almost immediately, so a single `kernel.tick_once()` call — as
  a literal reading of "a real Kernel run" might suggest — is not sufficient; the entity's brain
  never gets scheduled on tick 0. `test_information_need_detector_fires_from_execute_brain` instead
  loops up to 100 ticks (the worst-case `SURVIVAL`-mode cadence) and asserts on the first tick the
  project actually appears, rather than asserting after exactly one tick. This is a genuine
  scheduling-cadence finding not called out in the plan's Step 1 Verify text, not a plan error to
  fix.
- **Step 4 — doc fix beyond plan's explicit ask.** In addition to the wiring change, also updated
  `NearDeathHardeningPhase.apply()`'s own docstring "Effect:" list to mention the new
  `EmotionalModel` update (previously only listed `CombatUpdate.max_hp_delta += 5`). Not explicitly
  requested by Step 4's text, but the same "keep the self-declared contract honest" reasoning
  architecture-review applied to Step 1's `CognitionDomain` docstring fix applies here too — doc-only,
  no behavior change.
