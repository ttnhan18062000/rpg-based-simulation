---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-LEAD-CONTRADICTION-WIRING
artifact_type: plan
tags: [information, strategy, cognition]
---

# Implementation Plan — TCK-20260824-LEAD-CONTRADICTION-WIRING

## Summary

Wire the two orphaned contradiction systems into live production paths with no new feature flag
and no new durable state. `LeadContradictionSystem.enforce()` gets a single always-on
`run_phase("lead_contradiction", ...)` call inserted between `strategic_intelligence` (#31) and
`near_death_hardening` (#32) in `src/engine/pipeline.py`'s `refine()`. `_is_lead_contradicted()`
(`src/engine/pipeline_phases/lead_contradiction.py`) gains three new state-scan branches
(OBJECT/EVENT/CONCEPT) alongside the untouched existing LOCATION/PERSON/resource/information
branches. `BeliefContradictionService.detect()` gets a real caller by fixing
`ObservationBeliefBridge.process_observation()` (`src/domains/information/bridge.py`) to actually
invoke it for `claim_failed_search`/`region_danger_seen`, and by adding a same-tick
observation-synthesis step to `InformationBeliefPhase.apply()` (`src/domains/information/phase.py`,
already the `information_belief` phase, #5) that reads two EXISTING typed fields —
`entity.navigation.last_failure_reason` correlated against the actor's active
`ObjectiveState.target` for `claim_failed_search`, and `entity.navigation.region_id` correlated
against `state.local_scars` (via `state.regions[region_id].bounds`, no new import) for
`region_danger_seen` — and calls the fixed bridge. STRAT-230's `text`/`v2_evidence` is broadened
(not duplicated) to cover the wider `_is_lead_contradicted()` law. One genuine architectural gap
was found during fact-verification (see Unresolved Questions) that the orchestrator's five binding
decisions do not resolve: `refine()`'s return type (`StateUpdate` only, no event-carrying field)
means `LeadContradictionSystem.enforce()`'s own `List[SimulationEvent]` return value cannot survive
a `refine()` call today, which affects how literally AC1's "produces ... events" wording can be
satisfied by a `refine()`-driven test.

## Steps

### Step 1 — Wire `LeadContradictionSystem.enforce()` into `refine()`

**Files:** `src/engine/pipeline.py`

**Change:** Insert a new `run_phase("lead_contradiction", ...)` call between the existing
`strategic_intelligence` call and the existing `near_death_hardening` call
(`src/engine/pipeline.py:354-356`, confirmed by direct read — exact current lines are:
```
354: update = run_phase("strategic_intelligence", update, lambda u: StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))
356: update = run_phase("near_death_hardening", update, lambda u: AuthoritativeApplyPipeline._apply_near_death_hardening(state, u))
```
). `run_phase`'s signature is `run_phase(phase_name: str, upd: StateUpdate, phase_fn, feature_flag: Optional[str] = None) -> StateUpdate` (`pipeline.py:102`) — omit the fourth argument entirely (no flag), matching the binding no-flag decision and the existing no-flag `strategic_intelligence`/`contracts` calls at the same call site style.

`LeadContradictionSystem.enforce(state, update)` returns `Tuple[StateUpdate, List[SimulationEvent]]`
(confirmed `lead_contradiction.py:110-120`), but `run_phase`'s `phase_fn` contract requires a bare
`StateUpdate` return (confirmed: every other `phase_fn` lambda in `refine()` returns `StateUpdate`,
and the one existing tuple-returning phase, `WorldEmergencePhase.execute(...)`, is already unwrapped
at the call site via `...)[0]` — `pipeline.py:311`). Add a new private static method
`AuthoritativeApplyPipeline._enforce_lead_contradiction(state, u)` next to the existing
`_apply_near_death_hardening` method (`pipeline.py:438`), following the exact same
naming/placement convention:
```python
@staticmethod
def _enforce_lead_contradiction(state: "AuthoritativeState", update: StateUpdate) -> StateUpdate:
    from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
    new_update, _events = LeadContradictionSystem.enforce(state, update)
    # _events intentionally discarded at this boundary -- see plan.md Unresolved Questions:
    # refine() has no StateUpdate field that can carry List[SimulationEvent] out (same
    # limitation WorldEmergencePhase.execute()[0] already lives with at pipeline.py:311).
    return new_update
```
Call site: `update = run_phase("lead_contradiction", update, lambda u: AuthoritativeApplyPipeline._enforce_lead_contradiction(state, u))`.

`LeadContradictionSystem.enforce()` already takes `update` as an argument and merges into it via
`entity_updates = dict(update.entity_updates)` (`lead_contradiction.py:123`) and
`providers_update = dict(update.information_providers_update)` (`lead_contradiction.py:124`) — it
never constructs a fresh `StateUpdate()`. Passing `u` straight through (not `StateUpdate()`) is
therefore already correct in `.enforce()` itself; this step must not change that. This is the exact
`CombatEngagementPhase` bug shape (`pipeline.py:266-276`) to avoid — verify the diff shows `u` (not
a fresh `StateUpdate()`) reaching `.enforce()`.

**Other writers to the phase-ordering position / `update.entity_updates` at this exact point in
`refine()`:** `strategic_intelligence` (`StrategicIntelligenceSystem.fused_strategic_pass`, the
immediately-preceding phase) is the tick's authoritative owner of lead add/remove/suppress logic
and already merges (not replaces) into `EntityUpdate.strategic` (confirmed via
`intelligence.py:405-438` per investigation.md). `near_death_hardening` (immediately following) only
touches `.combat`/`.attributes` per its `PhaseDependencyGraph.PHASES` entry
(`src/engine/phase_graph.py:55`: writes `{"combat", "attributes"}`), not `.strategic`, so there is
no write-order collision with the new phase on the strategic aspect. No new registration in
`PhaseDependencyGraph.PHASES` is needed: confirmed `should_run_phase()` returns `True`
unconditionally for any `phase_name not in PhaseDependencyGraph.PHASES`
(`src/engine/phase_graph.py:82-83`) — `"lead_contradiction"` is not and does not need to be added to
that dict, closing investigation.md's Risk #4 with direct evidence.

**Do NOT touch:** `PhaseDependencyGraph.PHASES` (no entry needed, confirmed above),
`StrategicIntelligenceSystem.fused_strategic_pass`, `_apply_near_death_hardening`'s own body, and
the `strategic_intelligence`/`near_death_hardening` `run_phase` calls' own arguments (no flag
change to either).

**Verify:** new test 1 (`test_pipeline_refine_produces_lead_contradiction_matching_isolated_enforce`)
— see Step 9, scoped per the Unresolved Question resolution.

---

### Step 2 — Extend `_is_lead_contradicted()`: OBJECT lead coverage

**Files:** `src/engine/pipeline_phases/lead_contradiction.py`

**Change:** Add a new branch after the existing `"person"` branch (`lead_contradiction.py:79-88`)
and before the existing `"information"` branch (`:90-94`):
```python
if lead_kind == "object":
    for gi in state.ground_items.values():
        if gi.item_id == subject:
            return False
    for chest in state.chests.values():
        for item in chest.items:
            if item.item_id == subject:
                return False
    return True
```
Confirmed real fields: `GroundItemState.item_id: str` (`src/core/state.py:948`),
`ChestState.items: List[ItemStack]` (`src/core/state.py:1000`), `ItemStack.item_id: str`
(`src/core/models/inventory.py:26`). Use a plain string literal `"object"`, not
`LeadKind.OBJECT` — `LeadKind(str, Enum)` values equal their lowercase string
(`src/core/strategic.py:42-56`), so string-literal comparison already works identically to the
enum for every existing branch in this file (`lead_contradiction.py` does not currently import
`LeadKind` at all — no import needed for consistency with the file's existing style).

Note the polarity is intentionally the opposite of the `"location"`/`"resource"` branches above it:
those return `False` (not contradicted) when no matching node is found, because a resource node's
registry entry persists structurally even when depleted (absence there means "hasn't loaded this
tick yet," not "gone"). OBJECT leads point at ephemeral ground-item/chest spawns, so absence from
both registries is itself the failure signal per the binding scope decision — this asymmetry is
deliberate, not a bug, and must not be "fixed" to match the LOCATION polarity.

**Do NOT touch:** the `"resource"`, `"location"`, `"person"`, `"information"` branches above/below
this insertion — leave byte-for-byte unchanged (test 8 in Step 9 guards this).

**Verify:** new tests 5 (`test_object_lead_contradicted_when_item_absent_from_world` +
`test_object_lead_not_contradicted_when_item_present`).

---

### Step 3 — Extend `_is_lead_contradicted()`: EVENT lead coverage

**Files:** `src/engine/pipeline_phases/lead_contradiction.py`

**Change:** Add, immediately after the Step 2 OBJECT branch:
```python
if lead_kind == "event":
    for scar in state.local_scars.values():
        if scar.source_event_id == subject:
            return False
    return True
```
Confirmed real field: `LocalScarState.source_event_id: Optional[str] = None`
(`src/core/state.py:184`). This is a stronger, more precise match than investigation.md's
own flagged uncertainty ("no obvious existing helper") suggested was available —
`source_event_id` is exactly the field that ties a scar back to the originating world event, and it
follows the exact same "scan `state.<registry>.values()` for a `subject`-matching field" shape
already used by every other branch in this function (resource/location match `yields_item`, person
matches entity id, object now matches `item_id`). No new helper, no new import, and no cross-module
dependency on `src/engine/domain/view.py::DomainView` (a region-lookup helper exists there
(`get_region_for_position`), but region containment is not needed here — `source_event_id` gives a
direct, exact match against `lead.subject`).

This is the conservative heuristic the binding decision calls for: an EVENT lead is contradicted
only when there is no local scar still attributable to it, never a broader "is this world event
still true" judgment.

**Do NOT touch:** `state.recent_world_events` / `WorldEvent` — investigation.md flagged this as a
candidate surface too, but the binding decision narrows the check to `state.local_scars` only; do
not widen to also scan `recent_world_events`.

**Verify:** new tests 6 (`test_event_lead_contradicted_when_world_event_no_longer_active` +
`test_event_lead_not_contradicted_when_event_still_active`).

---

### Step 4 — Extend `_is_lead_contradicted()`: CONCEPT lead (explicit no-op)

**Files:** `src/engine/pipeline_phases/lead_contradiction.py`

**Change:** Add, immediately after the Step 3 EVENT branch and before the existing final
`return False` (`lead_contradiction.py:96`):
```python
if lead_kind == "concept":
    # CONCEPT contradiction is observation-shaped (tied to a failed paid-information
    # query outcome), not state-scan-shaped like the branches above. Deliberately routed
    # through BeliefContradictionService.detect() instead (see Step 5-7) -- this mirrors
    # the existing "information"-kind no-op above. Not an oversight.
    return False
```
This is a deliberate design choice per the binding decision, matching the existing precedent already
set for `"information"`-kind leads at `lead_contradiction.py:90-94`. Functionally this branch is
redundant with the function's existing final `return False` fallthrough — it is added explicitly
(rather than left to fall through silently) so the design intent is visible in the source, satisfying
the requirement that this be documented as deliberate rather than discoverable only by its absence.

**Do NOT touch:** do not add any `state.<registry>` scan for CONCEPT leads in this function — that
would contradict the binding decision that CONCEPT contradiction lives entirely in
`BeliefContradictionService.detect()`'s call site (Steps 5-7), not here.

**Verify:** new test 7, whichever variant matches this branch
(`test_concept_lead_contradicted_when_no_provider_knows_domain`-style test asserting the branch
always returns `False` regardless of world state — the actual CONCEPT contradiction behavior is
tested via Step 6/7's tests instead).

---

### Step 5 — Fix `ObservationBeliefBridge.process_observation()` to call `BeliefContradictionService.detect()`

**Files:** `src/domains/information/bridge.py`

**Change:** Current code (`bridge.py:44-52`) hand-builds a `CONTRADICTION`-shaped raw response dict
for `claim_failed_search` only, and routes it through `InformationResponseNormalizer.normalize()` +
`InformationAssimilationService.assimilate()` — it never calls
`BeliefContradictionService.detect()` (confirmed: no reference to `contradiction.py` anywhere in
`bridge.py`), and has no branch at all for `region_danger_seen`.

Replace with: for `obs_kind in ("claim_failed_search", "region_danger_seen")`, call
`BeliefContradictionService.detect(entity, event, state)` (`src/domains/information/contradiction.py:31-36`,
confirmed signature `detect(entity: EntityState, observation: Dict[str, Any], state: AuthoritativeState) -> BeliefContradictionResult`).
If `result.contradiction_detected` is `False`, return a no-op `InformationAssimilationResult()`
(mirrors `LeadContradictionSystem.enforce()` skipping non-contradicted leads entirely — no
mutation). If `True`, look up the actual `LeadState` via `entity.strategic.leads.get(result.lead_id)`
(`BeliefContradictionResult` only carries `lead_id: Optional[str]`, not the full lead —
confirmed `contradiction.py:17-23`) and translate:
```python
from dataclasses import replace as _replace
from src.core.updates import StrategicUpdate

failed_lead = _replace(
    lead,
    certainty=result.new_certainty,
    tested=True,
    test_outcome="FAILURE",
    failure_count=lead.failure_count + 1,
)
return InformationAssimilationResult(
    strategic_update=StrategicUpdate(leads_add_or_update=[failed_lead]),
    trace={"reason": result.reason, "observation_kind": obs_kind},
)
```
— mirroring exactly the typed-update pattern `LeadContradictionSystem.enforce()` already uses at
`lead_contradiction.py:152-159` (never a direct mutation of `entity.strategic.leads`). Add
`from src.core.updates import StrategicUpdate` to `bridge.py`'s imports (not currently imported
there — confirmed via the file's current import block, `bridge.py:9-14`). The existing default path
(the `KNOWN_FACT`/normalize/assimilate branch, `bridge.py:37-55`) is preserved unchanged for every
other `obs_kind`.

**Other writers to `entity.strategic.leads` this call site must not collide with:** none directly —
`process_observation()` itself does not run per-tick yet (Step 6/7 give it a caller); its output
(`InformationAssimilationResult.strategic_update`) is merged into `entity_updates[actor.id]` by the
caller in `InformationBeliefPhase.apply()`, not written here. See Step 6/7 for the merge-collision
analysis with that phase's other two branches.

**Do NOT touch:** `BeliefContradictionService.detect()` itself (`contradiction.py:31-76`) — no
change to its signature or its existing `claim_failed_search`/`region_danger_seen`-only logic. Do
not add a third `obs_kind` to `detect()`.

**Verify:** new tests 3 and 4 (Step 9) directly exercise this fixed bridge method.

---

### Step 6 — `InformationBeliefPhase.apply()`: synthesize `claim_failed_search` observations

**Files:** `src/domains/information/phase.py`

**Change:** `InformationBeliefPhase.apply()` currently has two mutually-adjacent branches per actor
inside its `for actor in actors:` loop (`phase.py:54-105`): branch (2) assimilates
`pending_responses` and unconditionally sets `entity_updates[actor.id] = EntityUpdate(...)`
(`phase.py:73-82`); branch (3) routes a new query for the first unresolved `UnknownFact`, gated by
`if actor.id not in entity_updates` (`phase.py:85`) so it only runs when branch (2) did not already
write this actor.

Add a third branch, after branch (3), that runs for every actor with a non-EXHAUSTED, untested
lead, regardless of whether branches (2)/(3) already wrote an entry for that actor this tick:

For each `lead in actor.strategic.leads.values()` where `lead.tested is False` and
`lead.certainty != LeadCertainty.EXHAUSTED`: if `actor.navigation.last_failure_reason is not None`
(confirmed real field `NavigationComponent.last_failure_reason: Optional[str]`,
`src/core/state.py:365`, set via `src/engine/apply.py:544` and `src/engine/patches.py:260` per
investigation.md, both confirmed by direct read) AND the actor has an active objective whose
`target` matches the lead's `subject` — resolved via
`actor.strategic.projects.get(actor.strategic.current_project_id)` →
find the objective in that project's `.objectives` list whose `.id == actor.strategic.current_objective_id`
→ check `.target == lead.subject` (confirmed real fields: `StrategicComponent.projects: Dict[str, ProjectState]`,
`.current_project_id`, `.current_objective_id` at `src/core/strategic.py:374,385-386`;
`ProjectState.objectives: List[ObjectiveState]` at `:277`; `ObjectiveState.target: Optional[str]` at
`:263`) — synthesize `{"kind": "claim_failed_search", "subject": lead.subject, "lead_id": lead.id, "location_searched": lead.detail, "details": {}}` and call
`ObservationBeliefBridge.process_observation(actor, obs_event, state)`.

Merge the result: `assim.strategic_update` must be merged into whatever `EntityUpdate` branches
(2)/(3) may already have written for this actor, using `EntityUpdate.merge()`
(confirmed to exist at `src/core/updates.py:677-708` — investigation.md's claim that "EntityUpdate
has no generic merge" is incorrect and is corrected here by direct read):
```python
if assim.strategic_update is not None:
    new_ent_upd = EntityUpdate(entity_id=actor.id, strategic=assim.strategic_update)
    existing = entity_updates.get(actor.id)
    entity_updates[actor.id] = existing.merge(new_ent_upd) if existing is not None else new_ent_upd
```
**Critical anti-drift hazard (not previously flagged in investigation.md):** `EntityUpdate.merge()`
merges `.strategic` via `self.strategic.merge(other.strategic)` (a real deep merge, safe), but
`.self_model_bundle_set` is merged via simple non-None preference —
`if other.self_model_bundle_set is not None: changes["self_model_bundle_set"] = other.self_model_bundle_set`
(`updates.py:704`) — this is NOT a deep merge. Branch (2) (pending-response assimilation) already
sets `self_model_bundle_set=new_self_model` (`phase.py:81`). If this new branch also sets
`self_model_bundle_set` (it should not, here — the observation-synthesis path only ever needs
`.strategic`, never touches `self_model.knowledge`), calling `existing.merge(new_ent_upd)` with a
`new_ent_upd` whose `self_model_bundle_set` is `None` is safe (branch (2)'s value is preserved,
since `other.self_model_bundle_set is not None` is `False`). Do not set `self_model_bundle_set` on
`new_ent_upd` in this step — only `strategic`. If a future change needs to touch
`self_model_bundle_set` from this branch too, it must build on top of `existing.self_model_bundle_set`
(if already set) rather than fresh off `actor.self_model`, or it will silently drop branch (2)'s
knowledge-model update.

**Other writers to `entity_updates[actor.id]` inside this same `apply()` call:** branch (2)
(pending-response assimilation, unconditional per actor) and branch (3) (unknown-routing, gated on
`actor.id not in entity_updates`) — both already enumerated above; this step's write must always go
through `EntityUpdate.merge()` against whatever is already in the dict, never a bare assignment,
unlike branch (2)/(3) which is safe to bare-assign only because they are mutually exclusive with
each other (a real gate) but this new branch is not mutually exclusive with either.

**Do NOT touch:** branches (2) and (3)'s own logic, gating, or field usage — only add the new
third branch and its merge into the shared `entity_updates` dict.

**Verify:** new test 3 (`test_claim_failed_search_observation_triggers_belief_contradiction_via_production_path`).

---

### Step 7 — `InformationBeliefPhase.apply()`: synthesize `region_danger_seen` observations

**Files:** `src/domains/information/phase.py`

**Change:** In the same new branch added in Step 6 (same per-actor loop iteration), additionally:
for each `lead in actor.strategic.leads.values()` where `lead.kind == "location"` and
`lead.certainty in (LeadCertainty.VAGUE, LeadCertainty.APPROXIMATE)` (matching
`BeliefContradictionService.detect()`'s own existing guard at `contradiction.py:61`) and
`lead.detail == actor.navigation.region_id` (confirmed real field
`NavigationComponent.region_id: Optional[str]`, `src/core/state.py:377`) — check whether the
actor's current region has an active local scar:
```python
region_id = actor.navigation.region_id
region = state.regions.get(region_id) if region_id else None
has_active_scar = False
if region is not None:
    x_min, y_min, x_max, y_max = region.bounds
    for scar in state.local_scars.values():
        sx, sy = scar.position
        if x_min <= sx <= x_max and y_min <= sy <= y_max:
            has_active_scar = True
            break
```
(Confirmed real fields: `RegionState.bounds: tuple[int,int,int,int]` and
`state.regions: Dict[str, RegionState]` at `src/core/state.py:238-240,1102`;
`LocalScarState.position: tuple[float,float]` at `:179`.) This inlines the same
containment check `DomainView.get_region_for_position` (`src/engine/domain/view.py:47-68`)
already performs, without importing it — `src/domains/information/phase.py` importing from
`src/engine/domain/view.py` would be a new `domains -> engine` coupling not currently exercised by
any pinned exception in `tests/architecture/test_phase18_import_boundaries.py` (that test only
pins `systems -> engine` exceptions, `test_systems_do_not_import_engine_outside_pinned_exceptions`,
lines 200-243; there is no equivalent `domains -> engine` test today, but introducing a new
cross-layer import here is unnecessary when the same bounds check is three lines of inline code
against already-available `RegionState`/`LocalScarState` fields).

If `has_active_scar`, synthesize `{"kind": "region_danger_seen", "subject": lead.subject, "region_id": region_id, "details": {}}` and call `ObservationBeliefBridge.process_observation(actor, obs_event, state)`,
merging the result exactly as in Step 6 (same `EntityUpdate.merge()` pattern, same
`self_model_bundle_set` hazard note applies).

**Do NOT touch:** `src/engine/domain/view.py::DomainView` — do not import it into
`src/domains/information/phase.py`; the inline bounds check above is the deliberate substitute.

**Verify:** new test 4 (`test_region_danger_seen_observation_triggers_belief_contradiction_via_production_path`),
including its required negative case (PRECISE-certainty lead not degraded — already covered by
`detect()`'s own existing guard, reused here unchanged).

---

### Step 8 — Broaden STRAT-230's parity ledger entry

**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** STRAT-230 (`docs/parity_ledger/strategic_cognition.yaml:2625-2646`, confirmed by direct
read) currently has `status: verified`, `text` describing only the resource/person-destination
case, `v2_evidence` citing `LeadContradictionSystem.enforce()` with no mention that it was unwired,
and `test_path` pointing only at the isolated `.enforce()` unit test. Edit only this entry:
- `text`: broaden to also cover OBJECT (ground item/chest absence) and EVENT (no matching active
  `local_scars` record) contradiction, and note the phase is now invoked every tick from
  `AuthoritativeApplyPipeline.refine()` (not just callable in isolation). Do not create a second
  STRAT-2xx entry — this is a single law with wider coverage, per the binding decision.
- `v2_evidence`: keep the existing citations, add the new `run_phase("lead_contradiction", ...)`
  call site (`src/engine/pipeline.py`, insertion point from Step 1).
- `test_path`: append the new full-pipeline test from Step 9 test 1, separated by `;` from the
  existing `test_path` value — do not replace the existing isolated-unit test path, both remain
  valid regression coverage per the binding decision.
- `status`: keep `verified` (unchanged).

Use a minimal, targeted YAML edit — do not run a full-file parity-updater rewrite tool. After
editing, run `git diff --stat docs/parity_ledger/strategic_cognition.yaml` and confirm only the
STRAT-230 entry's lines changed (this file is 3800+ lines; a round-trip YAML dump can silently
reformat the whole file — known failure mode, see project memory on parity-updater full-file
rewrite risk).

**Other writers to `strategic_cognition.yaml`:** none from this ticket's other steps — this is the
only file in the ledger this ticket touches (confirmed: investigation.md's file-wide scan found no
other entry referencing `lead_contradiction.py`/`contradiction.py`/`BeliefContradictionService` in
the portion reviewed).

**Do NOT touch:** any other STRAT-* entry in this file, and do not touch
`docs/parity_ledger/strategic_cognition.yaml`'s schema/structure beyond this one entry's fields.

**Verify:** `pytest tests/tools/test_parity_index.py -v` (structural/duplicate-ID checks pass).

---

### Step 9 — Tests

**Files:** `tests/unit/cognition/test_information_seeking.py`,
`tests/unit/domains/information/test_phase5_belief_contradiction.py` (or a new
`tests/unit/domains/information/test_phase5_information_belief_phase.py` if the call site's tests
don't fit the existing file — check first),
`tests/unit/observability/test_event_extractor_information2.py` (Step 10's new diff rules — this is
the existing file already covering `lead_certainty_updated`/`belief_stale`, confirmed via
investigation.md), `docs/parity_ledger/strategic_cognition.yaml` (test_path pointer only, see Step 8).

**Change:** Add the 8 new tests specified in `test_plan.md`'s "New Tests Required" section
(items 1-8; item 9 is the Step 8 pointer update, not a new test):
1. `test_pipeline_refine_produces_lead_contradiction_matching_isolated_enforce` — per the Decisions
   Log's Option A resolution: assert BOTH (a) `StateUpdate.entity_updates[...].strategic` and
   `information_providers_update` mutations from a `refine()` call are identical to a direct
   `.enforce()` call on the same input state, AND (b) calling `EventExtractor.extract(prior_state,
   post_refine_state, refined_update, mode)` after the `refine()` call yields `belief_contradiction`
   and `lead_contradiction_resolved` `SimulationEvent`s with payloads matching (by `lead_id`,
   `subject`, `failure_count`, and `old_certainty`/`provider_id` for the former) what `.enforce()`
   returns directly in its own `List[SimulationEvent]` — this is what makes AC1's literal wording
   true per Step 10.
2. `test_pipeline_refine_skips_lead_contradiction_when_flag_off` — **drop this test as scoped in
   test_plan.md**: there is no `ENABLE_LEAD_CONTRADICTION` flag per the binding no-flag decision, so
   a flag-off regression test has no subject. Do not add a flag-off test.
3. `test_claim_failed_search_observation_triggers_belief_contradiction_via_production_path` (Step 6).
4. `test_region_danger_seen_observation_triggers_belief_contradiction_via_production_path` (Step 7),
   including the negative PRECISE-certainty case.
5. `test_object_lead_contradicted_when_item_absent_from_world` +
   `test_object_lead_not_contradicted_when_item_present` (Step 2).
6. `test_event_lead_contradicted_when_world_event_no_longer_active` +
   `test_event_lead_not_contradicted_when_event_still_active` (Step 3).
7. `test_concept_lead_contradicted_when_no_provider_knows_domain`-style test asserting the CONCEPT
   branch always returns `False` from `_is_lead_contradicted()` (Step 4).
8. `test_is_lead_contradicted_resource_literal_remains_dead_code` — assert `"location"`/`"person"`
   behavior is byte-for-byte unchanged (regression guard for Steps 2-4).

Run the full scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands" section after
each step, not just at the end.

**Do NOT touch:** `tests/unit/strategic/test_belief_cycle.py`,
`tests/unit/strategic/test_detour_suggestion.py` — these are regression guards (must show zero
diff in behavior), not tests to modify.

**Verify:** all listed scoped pytest commands pass; `tests/architecture/test_phase18_import_boundaries.py`
passes (confirms no accidental new `domains -> engine` import from Step 7's inline-bounds-check
choice).

### Step 10 — Extend `EventExtractor.extract()`: `belief_contradiction` / `lead_contradiction_resolved` diff rules

**Files:** `src/observability/event_extractor.py`

**Change:** Per the Decisions Log above (Option A), add two new diff-based event rules inside the
existing `if not _push_shapers_phase2_active and hasattr(entity, "strategic") and
hasattr(prior_ent, "strategic"):` block (`event_extractor.py:775-823`), in the same
`for lid, lead in curr_leads.items(): prior_lead = prior_leads.get(lid)` loop that already derives
`lead_certainty_changed`/`lead_certainty_updated`/`belief_stale`. Add, immediately after the
existing `lead_certainty_updated` append (`:805`) and before the `belief_stale` check (`:806`):

```python
# belief_contradiction / lead_contradiction_resolved (this ticket): fires when
# LeadContradictionSystem.enforce() (run_phase "lead_contradiction", Step 1) has just
# transitioned this lead to EXHAUSTED + test_outcome="FAILURE" this tick. Mirrors the exact
# payload shape LeadContradictionSystem.enforce() itself builds at
# lead_contradiction.py:216-231/234-245 so a refine()-driven test observes identical events
# to a direct .enforce() call.
_prior_failed = (
    prior_lead is not None
    and getattr(prior_lead, "test_outcome", None) == "FAILURE"
    and getattr(prior_lead.certainty, "value", str(prior_lead.certainty)) == "EXHAUSTED"
)
_curr_failed = (
    getattr(lead, "test_outcome", None) == "FAILURE"
    and getattr(lead.certainty, "value", str(lead.certainty)) == "EXHAUSTED"
)
if prior_lead is not None and _curr_failed and not _prior_failed:
    events.append(SimulationEvent(
        event_type="belief_contradiction", event_category="strategy",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="lead_contradiction_system", message="",
        payload={
            "lead_id": lid,
            "provider_id": getattr(lead, "source_entity_id", None),
            "subject": lead.subject,
            "old_certainty": getattr(prior_lead.certainty, "value", str(prior_lead.certainty)),
            "failure_count": lead.failure_count,
        },
    ))
    events.append(SimulationEvent(
        event_type="lead_contradiction_resolved", event_category="strategy",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="lead_contradiction_system", message="",
        payload={
            "lead_id": lid,
            "subject": lead.subject,
            "failure_count": lead.failure_count,
        },
    ))
```

Confirmed real fields/values (via direct read of `lead_contradiction.py:150-232`):
`LeadContradictionSystem.enforce()` sets `certainty=LeadCertainty.EXHAUSTED, tested=True,
test_outcome="FAILURE", failure_count=lead.failure_count + 1` on the failed lead, decrements the
provider's `reliability_score` (not re-derived here — that's a separate,
already-diffable-if-needed provider-state concern, out of this step's scope: `event_extractor.py`
has no existing provider-reliability diff rule and this ticket does not add one; the ticket's ACs
only require the two lead-scoped events), and emits `belief_contradiction` with payload keys
`lead_id`/`provider_id`/`subject`/`old_certainty`/`failure_count`, then `lead_contradiction_resolved`
with payload keys `lead_id`/`subject`/`failure_count` — the new diff rule above reproduces both
payload shapes exactly from post-tick `lead` + pre-tick `prior_lead`, using `source_entity_id` off
the **current** `lead` object (not `prior_lead`) since `source_entity_id` does not change across the
contradiction transition (confirmed: `LeadContradictionSystem.enforce()` never mutates
`source_entity_id` on `failed_lead`, only `certainty`/`tested`/`test_outcome`/`failure_count`).

The `_prior_failed`/`_curr_failed` guard exists so a lead that was *already* EXHAUSTED+FAILURE last
tick (e.g. the entity re-observed an already-exhausted lead) does not re-emit the event every tick —
mirrors `LeadContradictionSystem.enforce()`'s own idempotency guard at `lead_contradiction.py:141-142`
(`if lead.test_outcome == "FAILURE": continue`).

This block sits behind the same `_push_shapers_phase2_active` flag-off rollback path as
`lead_certainty_changed`/`lead_certainty_updated`/`belief_stale` — no new flag is introduced, this
new code simply lives inside the existing conditional exactly like its neighbors, consistent with
the no-new-flag binding decision.

**Other writers to this event list in the same `extract()` call:** the pre-existing
`lead_certainty_changed`/`lead_certainty_updated`/`belief_stale`/`decision_diverged_by_belief`/
`decision_divergence_detected` rules in the same loop/block — all additive appends to the same
`events` list per entity, no collision (each rule's `if` condition is independent).

**Do NOT touch:** `_push_shapers_phase2_active`'s own gating logic, any other event rule in this
function, or `EventExtractor`'s public signature (`extract(prior_state, current_state, update,
mode)`) — this step only adds two new `events.append(...)` calls inside an existing loop.

**Verify:** new test 1 (Step 9, revised) asserts these two events are present and payload-identical
to a direct `.enforce()` call, via `EventExtractor.extract(prior_state, post_refine_state,
refined_update, mode)` after a `pipeline.refine()` call.

---

## Scope Guards

- Do not touch `BeliefCycleSystem` (`src/systems/strategic_systems/belief.py`) or its call site in
  `src/systems/strategic_systems/intelligence.py:405-438` — separate, already-wired, already-correct
  hostile-proximity contradiction mechanism for `location`-kind leads. Not the same system as
  `BeliefContradictionService`.
- Do not touch `LeadRoutingSystem` (`src/engine/domain/lead_routing.py`) or
  `DetourSuggestionSystem` (`src/systems/strategic_systems/detour.py`) — routing/bandwidth-eviction
  is adjacent to, not part of, contradiction-testing.
- Do not add any feature flag (no `ENABLE_LEAD_CONTRADICTION` or equivalent) — the ticket's own
  Request Summary explicitly forbids this.
- Do not widen `BeliefContradictionService.detect()`'s own signature or its existing
  `claim_failed_search`/`region_danger_seen`-only logic (`contradiction.py:31-76`) — only its caller
  changes (Steps 5-7).
- Do not add any new field to `AuthoritativeState`, `EntityState`, `StateUpdate`, or `EntityUpdate`
  — every step above uses only fields already confirmed to exist by direct file read.
- Do not register `"lead_contradiction"` in `PhaseDependencyGraph.PHASES`
  (`src/engine/phase_graph.py`) — confirmed unnecessary (Step 1).
- Do not import `src.engine.domain.view.DomainView` into `src/domains/information/phase.py`
  (Step 7) — use the inline bounds check instead.
- Do not update `docs/engine/authoritative_pipeline.md`'s phase count/table or
  `docs/mechanics/04_strategic_cognition.md`/`docs/simulation/domains/information_contract.md` as
  part of these implementation steps — those are doc-updater-phase deliverables outside this
  plan's Steps (the standard-tier pipeline's Docs phase handles them separately); this plan only
  covers the STRAT-230 parity-ledger edit the ticket's own Scope section lists.
- Do not remove the dead `"resource"` branch in `_is_lead_contradicted()` — leave it as inert dead
  code (documented choice, Step 2/4 area); do not invent a production caller for `kind="resource"`.
- Do not touch the `"information"`-kind no-op branch (`lead_contradiction.py:90-94`).

## Dependency Map

- Step 1 (pipeline wiring) — independent, no dependency on other steps.
- Steps 2, 3, 4 (`_is_lead_contradicted()` OBJECT/EVENT/CONCEPT) — independent of each other and of
  Step 1; all three edit the same function but non-overlapping branches (can be done in any order,
  sequentially, to keep diffs reviewable).
- Step 5 (bridge.py fix) — must land before Steps 6 and 7 (both call the fixed
  `process_observation()`).
- Step 6 and Step 7 — both depend on Step 5; independent of each other (can be done in either
  order); both edit the same new branch in `phase.py`'s `apply()` so should land as one combined
  diff to `phase.py` in practice, but are separable for review/testing purposes.
- Step 8 (STRAT-230) — depends on Step 1 (needs the pipeline call site to cite), Step 10 (needs the
  event-derivation call site to cite), and on Step 9 test 1 existing (needs its real test path to
  cite in `test_path`) — do this step last among the non-test steps.
- Step 10 (`EventExtractor` diff rules) — depends on Step 1 (the phase must exist and run inside
  `refine()` for its state transition to be diffable); independent of Steps 2-7.
- Step 9 (tests) — each sub-test depends on its corresponding implementation step (1, 2, 3, 4, 6, 7,
  10 respectively) being complete first; test 1 specifically depends on both Step 1 AND Step 10.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: full `pipeline.refine()` tick produces `belief_contradiction`/`lead_contradiction_resolved` events and matching mutations vs. direct `.enforce()` | Steps 1, 10 | Step 9 test 1 (Option A, see Decisions Log) |
| AC2: `BeliefContradictionService.detect()` invoked from a real production call site for `claim_failed_search`/`region_danger_seen`, applied via typed `StrategicUpdate` | Steps 5, 6, 7 | Step 9 tests 3, 4 |
| AC3: `_is_lead_contradicted()` extended to cover OBJECT/CONCEPT/EVENT `LeadKind` values | Steps 2, 3, 4 | Step 9 tests 5, 6, 7, 8 |
| AC4: STRAT-230's `v2_evidence` updated with the new pipeline-level test | Step 8 | `pytest tests/tools/test_parity_index.py` + manual `git diff --stat` check |

## Decisions Log

**AC1 event-return-shape question — RESOLVED (human decision, recorded here per the requirement
that resolving an Unresolved Question removes/replaces the heading rather than leaving it
dangling):**

The question was how AC1's "produces `belief_contradiction`/`lead_contradiction_resolved` events"
can be satisfied by a bare `AuthoritativeApplyPipeline.refine()` call, given `refine()` returns only
`StateUpdate` (no field can carry a `List[SimulationEvent]` out — the one other tuple-returning
phase, `WorldEmergencePhase.execute()`, already has its second element silently discarded via
`...)[0]` at `pipeline.py:311`).

**Decision: Option A.** Extend `EventExtractor.extract()` (`src/observability/event_extractor.py`)
with two new diff-based rules for `belief_contradiction` and `lead_contradiction_resolved`,
mirroring the existing `lead_certainty_updated`/`belief_stale` pattern at
`event_extractor.py:769-823` (per-entity `curr_leads`/`prior_leads` diff by `lid`, inside the
existing `if not _push_shapers_phase2_active and hasattr(entity, "strategic") and
hasattr(prior_ent, "strategic"):` block). This makes AC1's literal wording true for a
`refine()`-driven tick, matches the codebase's own established event-derivation pattern, needs no
`StateUpdate` schema change, and is accepted scope for this ticket even though it touches a shared,
heavily-tested module not originally named in the ticket's Scope section — the ticket's own Related
Code Areas is being updated to add `src/observability/event_extractor.py` alongside this decision.
See Step 10 (new) for the concrete implementation, and the revised Step 9 test 1 for how it's
verified. Option B (StateUpdate-parity-only, no event derivation) was the alternative and is NOT
taken — the requester confirmed literal AC1 satisfaction is required.

## Deviations

Implementation followed all 10 steps as specified. Minor, non-substantive deviations during
Implement:

- **Steps 6/7 (`phase.py` new branch)**: the plan describes the `claim_failed_search` check (Step 6)
  and the `region_danger_seen` check (Step 7) as two passes over `actor.strategic.leads.values()`
  within the same per-actor loop iteration. The implementation combines both into a single `for
  lead in actor.strategic.leads.values():` pass per actor, computing `obs_event` from the
  `claim_failed_search` condition first and falling back to the `region_danger_seen` condition only
  if the first did not match (`obs_event is None`). This is functionally equivalent for every case
  the plan's own tests describe (a lead cannot simultaneously be the target of a
  `last_failure_reason`-linked objective and be evaluated for `region_danger_seen` in a way that
  changes outcome), and avoids a second full iteration over the same dict. Not a behavior change.
- **Step 9 test 3/4 location**: placed in a new file
  `tests/unit/domains/information/test_phase5_information_belief_phase.py` (the plan's own
  fallback option, since the call site lands in `phase.py` directly). Additionally added 3
  supplementary direct-unit tests to `tests/unit/domains/information/
  test_phase5_observation_belief_bridge.py` (`test_claim_failed_search_routes_through_belief_contradiction_service`,
  `test_region_danger_seen_routes_through_belief_contradiction_service`,
  `test_claim_failed_search_no_op_when_no_contradiction`) to isolate Step 5's bridge-level fix from
  Step 6/7's phase-level wiring — beyond the plan's 8-test minimum, not a replacement for any of
  them.
- **Step 9 test 2 (flag-off regression test)**: dropped per the ticket instructions and the plan's
  own no-flag binding decision — there is no `ENABLE_LEAD_CONTRADICTION` flag, so this test has no
  subject.
