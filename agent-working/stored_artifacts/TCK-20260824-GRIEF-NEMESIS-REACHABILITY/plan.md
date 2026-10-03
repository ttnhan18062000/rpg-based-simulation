---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-GRIEF-NEMESIS-REACHABILITY
artifact_type: plan
tags: [cognition, social, observability]
---

# Implementation Plan — TCK-20260824-GRIEF-NEMESIS-REACHABILITY

## Summary

This plan makes `CampaignOrchestrator.run_episode()` reachable from a real production/SimQ
entry point, adds `grief_urgency_triggered`/`nemesis_relation_formed` `SimulationEvent`s
queryable by the SOCIAL SimQ pillar, and extends grief-urgency (not nemesis — see Decisions
below) to trigger mid-episode on a live `entity_death`, through the authoritative
`StrategicUpdate`/`ApplyPath` route rather than `GriefUrgencyImporter`'s current direct-
`EntityState`-return shape. The approach reuses existing plumbing at every point verified
against source: the already-dormant `ENABLE_LIFE_ARC_CAMPAIGNS` feature flag
(`src/domains/optimization/feature_flags.py:58`) gates a new campaign-aware branch in
`tools/calibrate_simq.py`; the already-firing `event_extractor.py:483` lifecycle-transition
detection is extended (not replaced) to also queue a grief trigger; and the queued trigger is
drained and merged into `EntityUpdate.strategic` inside `Kernel._phase_resolution` — the exact
point where every other per-entity `EntityUpdate` already gets merged
(`src/engine/kernel.py:586-654`) before `AuthoritativeApplyPipeline.refine()` runs — so the
injection lands through `StrategicPatch.apply()` (`src/engine/patches.py:415-455`) like any
other tick-time strategic mutation, exactly the pattern `src/engine/tactical.py:186-196`
already uses. A death detected on an episode's FINAL tick has no tick N+1 within that `Kernel`
run to drain into via this route — Step 5b adds a narrow episode-teardown flush
(`Kernel.drain_pending_triggers_at_teardown()`, wired into
`ScenarioRuntimeService`/`CampaignOrchestrator.run_episode()`) so that case still lands within the
same episode, through the same `AuthoritativeApplyPipeline.refine()` +
`ApplyPath.apply_generation()` commit route a normal tick uses (verified neither step alone is
sufficient: `refine()` does not itself write `state.entities`, per `src/engine/pipeline.py:41` and
`src/engine/apply.py:189-243`).

## Decisions (committed, not left open)

**Decision 1 — SimQ campaign-mode entry point.** New campaign-aware branch inside
`tools/calibrate_simq.py`, not a separate parallel script. Read `_run_engine()`
(`tools/calibrate_simq.py:164-338`): it already has a `_resolve_profile()`/`_load_profile_feature_flags()`
pair that reads per-profile YAML keys before building the `Kernel`. A new sibling loader
(`_load_profile_campaign_episodes()`) reads a new `campaign_episodes:` integer key from a new
profile file `config/simulation_quality/profiles/campaign_life_arc.yaml`. When that key is present
and > 0, `main()` calls a new `_run_campaign_engine()` (parallel to `_run_engine()`, same
`(run_dir, elapsed, run_id)` return contract at `calibrate_simq.py:331-338`) instead of
`_run_engine()`. This reuses `ScenarioRuntimeService`/`CampaignOrchestrator`/`EventRecorder` (all
already exist) with the least duplication, per the investigation's own framing of the two options.
The new profile also sets `feature_flags: {ENABLE_LIFE_ARC_CAMPAIGNS: "ON"}` — verified this flag
is already registered (`src/domains/optimization/feature_flags.py:58`, default `FeatureMode.OFF`)
and already present in `calibrate_simq.py`'s `_KNOWN_FLAGS` list (`calibrate_simq.py:225`), but
verified (via `grep -rn "ENABLE_LIFE_ARC_CAMPAIGNS"`) it is otherwise **only** referenced by
`src/domains/optimization/degradation.py:62,64` as a bare string in a phase-skip name list for an
unrelated live-kernel degradation mechanism — it currently gates nothing that calls
`CampaignOrchestrator`. Turning it "ON" in the new profile is therefore a safe, semantically
correct reuse of an already-named-but-dormant flag, not a new flag needed. `degradation.py` is
NOT touched by this plan.

**Decision 2 — event_category and pillar: SOCIAL.** Verified both scorer files directly:
`src/simulation_quality/scorers/social.py:19-31` (`SocialScorer.EVENT_TYPES`) already covers
`social_memory_created`, `reputation_delta`, `group_joined`/`group_expelled` — all
entity-relationship-state signals sourced from social memory, the same family
grief/nemesis belong to (both are literally built from `entity.social.trust_history`
/`SocialMemoryRecord.interaction_history`). `src/simulation_quality/scorers/narrative.py:11-33`
(`NarrativeScorer`)'s own docstring states it "Does NOT duplicate FactionScorer signals" and its
`EVENT_TYPES` are quest/chronicle/scenario-milestone signals (`quest_completed`,
`chronicle_entry_created`, `scenario_stalled`) — a different semantic family. Both new event types
get `event_category="social"` and are wired into `SocialScorer`, not `NarrativeScorer`.

**Correction to investigation.md's framing of the `orchestrator.py:172` gap** (verified by reading
`src/engine/kernel.py:262-267` and `987-988`, and `src/engine/scenario_runtime.py:131-145,280-362`):
`Kernel.__init__` always builds its own `EventRecorder` (line 262) regardless of what is passed to
`ScenarioRuntimeService`, and `Kernel._phase_observability` always records every
`EventExtractor`-generated event (including the new `grief_urgency_triggered` event, Step 4) to
*that* recorder (`self._event_recorder.record(event)`, kernel.py:988) — which always writes its own
`data/runs/{run_id}/simulation_events.jsonl` (kernel.py:222-227). This happens **unconditionally**,
independent of the `ScenarioRuntimeService(spec, initial_state=..., event_recorder=...)` wiring.
`ScenarioRuntimeService._event_recorder` (scenario_runtime.py:131-145) is used **only** for its own
3 scenario-lifecycle events — `scenario_objective_completed`/`scenario_objective_progressed`
(lines 293-326) and `scenario_stalled` (347-362) — and `CampaignOrchestrator`'s own
`self._event_recorder` (separate object) is used only by `_emit_chronicle_events`
(orchestrator.py:308-336) and the new `_advance_nemesis_relations()`/`_advance_grief_urgencies()`
emissions added in Step 6. So the `orchestrator.py:172` fix (Step 2) does **not** block AC2/AC3 as
investigation.md implied — mid-episode Kernel-generated events reach their own episode-scoped JSONL
file regardless. The fix is still real and still required (those 3 scenario-lifecycle events are
silently dropped today), and Step 1's campaign runner still needs each episode's own `run_id` to
locate and merge its JSONL file — Step 1a covers that separately.

## Steps

### Step 1a — Expose each episode's `run_id` so the SimQ runner can find its JSONL file

**Files:** `src/engine/scenario_runtime.py`, `src/domains/campaigns/state.py`,
`src/domains/campaigns/orchestrator.py`

**Change:** `ScenarioRuntimeService` has no public `run_id` accessor today (confirmed: `grep -n
"run_id" src/engine/scenario_runtime.py` only matches internal `self._kernel` construction, not a
property; its only public properties are `tick`, `objective_state`, `alive_entity_count`,
`final_state` at scenario_runtime.py:220-255). Add:
```python
@property
def run_id(self) -> Optional[str]:
    """The underlying Kernel's run_id, or None if not yet started."""
    if self._kernel is None:
        return None
    return getattr(self._kernel, "_run_id", None)
```
`EpisodeSummary` (`src/domains/campaigns/state.py:166-186`) is a frozen dataclass with exactly
`episode_index: int`, `completed_tick: int`, `to_dict()`, and `from_dict()` — verified by reading
the class directly. Add `run_id: str = ""` as a third field (additive default, non-breaking), and
update both `to_dict()` (add `"run_id": self.run_id`) and `from_dict()` (add
`run_id=d.get("run_id", "")` — `.get` with default keeps old serialized records loadable). In
`CampaignOrchestrator.run_episode()` (`orchestrator.py:151-185`), after `svc.start()` succeeds
(line 174) and before `svc.abort()` (line 178), capture `episode_run_id = svc.run_id`, and pass it
into the `EpisodeSummary(...)` construction at line 180-183 as `run_id=episode_run_id or ""`.

**Do NOT touch:** `ScenarioRuntimeService`'s other properties or `_run_loop`/`_evaluate_after_tick`
internals — only add the one new property.

**Verify:** new unit test `test_scenario_runtime_exposes_run_id` in
`tests/unit/engine/` (or wherever `ScenarioRuntimeService` unit tests already live — confirm via
`test-scoper` at Test phase) asserting `svc.run_id is None` before `start()` and equals
`svc._kernel._run_id` after; extend `tests/unit/domains/campaigns/test_campaign_orchestrator.py`
with `test_episode_summary_carries_run_id`.

### Step 1b — Wire `self._event_recorder` through to `ScenarioRuntimeService`

**Files:** `src/domains/campaigns/orchestrator.py`

**Change:** At `orchestrator.py:172`, change
`svc = ScenarioRuntimeService(spec, initial_state=initial_state)` to
`svc = ScenarioRuntimeService(spec, initial_state=initial_state, event_recorder=self._event_recorder)`.
Per the Decisions section above, this makes `scenario_objective_completed`/
`scenario_objective_progressed`/`scenario_stalled` (scenario_runtime.py:293-362) reach
`CampaignOrchestrator`'s own recorder when one is supplied; it does not affect the per-tick
Kernel-generated events (those already reach their own per-episode recorder unconditionally,
confirmed above). **Other writers to `self._event_recorder` on `CampaignOrchestrator`**: only
`_emit_chronicle_events()` (orchestrator.py:308-336, already-existing writer) and the two new
writers added in Step 6 (`_advance_grief_urgencies`, `_advance_nemesis_relations`). This change adds
a fourth writer (indirectly, via `ScenarioRuntimeService`) to the same recorder object; all four are
additive `.record()` calls on the same `EventRecorder`, which is designed for concurrent-within-a-
thread sequential recording (no dict-key collision risk — `EventRecorder.record()` appends, per
kernel.py:987-988's identical usage). No ordering/race conflict: all of these run synchronously on
the same thread within `run_episode()`/`_advance_state()`.

**Do NOT touch:** any other `ScenarioRuntimeService(...)` construction site project-wide (per
investigation's anti-drift note) — only `orchestrator.py:172`.

**Verify:** new architecture-guard test `test_run_episode_passes_event_recorder_to_scenario_runtime`
in `tests/unit/domains/campaigns/test_campaign_orchestrator.py` (test_plan.md item 4) — spy/mock
`EventRecorder`, assert it received at least the `scenario_objective_completed` event after a
`run_episode()` call with a small `tick_limit` victory condition.

### Step 2 — Add the reconciled `StrategicUpdate`-returning builders to both importers

**Files:** `src/domains/campaigns/grief_urgency.py`

**Change:** Verified `GriefUrgencyImporter.apply()` (grief_urgency.py:43-63) and
`NemesisRelationImporter.apply()` (66-93) both build a `ConcernState`/`BlockerState` then
`dc_replace` a whole new `EntityState`. Verified `StrategicUpdate` (`src/core/updates.py:473-536`)
has exactly `concerns_add_or_update: list[ConcernState]` (493) and
`blockers_add_or_update: list[BlockerState]` (477) — the two fields these importers already build.
Add two new staticmethods, sharing the existing concern/blocker construction logic (extract it into
a small private helper each, e.g. `_build_grief_concern(modifier) -> ConcernState` and
`_build_nemesis_blocker(relation) -> BlockerState`, called by both the existing `.apply()` and the
new methods, so the two paths cannot drift):
```python
@staticmethod
def build_strategic_update(modifier: GriefUrgencyModifier) -> "StrategicUpdate":
    from src.core.updates import StrategicUpdate
    return StrategicUpdate(concerns_add_or_update=[GriefUrgencyImporter._build_grief_concern(modifier)])
```
and the symmetric `NemesisRelationImporter.build_strategic_update(relation) -> StrategicUpdate`
using `blockers_add_or_update`. The ticket's Scope explicitly names both
`GriefUrgencyImporter.apply()`/`NemesisRelationImporter.apply()` for this reconciliation — both get
the new method for architectural symmetry — but per AC3 (which only requires grief-urgency
mid-episode injection) and the Scope bullet's own wording ("the same grief-urgency concern
injection"), only `GriefUrgencyImporter.build_strategic_update()` is wired into a live call site
(Step 4/5). `NemesisRelationImporter.build_strategic_update()` is added but has no caller yet — this
is intentional, not a gap: nemesis-relation formation requires `NEMESIS_EPISODE_COUNT>=2` distinct
*episodes* of antagonism history (grief_urgency.py:27-30), which cannot be evaluated from a single
live episode's data, so it has no natural mid-episode trigger. A future ticket could wire it into
`_build_initial_state()` as a drop-in replacement for the direct-return path; out of scope here.

**Do NOT touch:** `GriefUrgencyImporter.apply()`/`NemesisRelationImporter.apply()`'s existing
signatures, return types, or behavior — `_build_initial_state()`'s call sites
(orchestrator.py:567-571, 576-579) must keep calling `.apply()` exactly as today.

**Verify:** `test_grief_urgency_importer_returns_strategic_update` (test_plan.md AC3, extends
`tests/unit/domains/campaigns/test_grief_urgency.py`) — asserts `build_strategic_update()` returns
a `StrategicUpdate(concerns_add_or_update=[...])` with the same `concern_id`/`urgency` shape
`.apply()` would have injected. Existing 30 tests in that file must keep passing unchanged.

### Step 3 — Add `PendingGriefTrigger` ephemeral Kernel-run bookkeeping (not durable state)

**Files:** `src/engine/kernel.py`

**Change:** Verified `Kernel`'s 7-phase loop (`kernel.py:344-427`: `_phase_init` → `_phase_scheduling`
→ `_phase_collection` → `_phase_resolution` → `_phase_cleanup` → `_phase_advancement` [which calls
`_phase_observability` at line 737] → `_phase_persistence`). `_phase_observability` runs strictly
after `_phase_resolution` has already called `AuthoritativeApplyPipeline.refine()` for that tick
(line 649), so a death detected in `_phase_observability` cannot be applied within the same tick's
`ApplyPath` pass — it must be applied in a later tick's `_phase_resolution`. Add a new `Kernel`
instance attribute (in `__slots__` at kernel.py:47 and initialized in `__init__` near the other
per-run bookkeeping fields, e.g. next to `self._final_results = []` at line 210):
`self._pending_grief_triggers: list = []`. This is **not** part of `AuthoritativeState` — it is
transient, in-process bookkeeping scoped to one `Kernel` instance's run, in the same category as
already-existing fields like `self._final_results`/`self._current_update`
(kernel.py:47,210,641/680) which also carry data across phases/ticks within a run without being
durable simulation state. It does not survive process restart, is not serialized, and is not part
of any replay/persistence contract — so it is exempt from the Durable State Rule's typed-model
requirement (which governs `AuthoritativeState`-resident data), matching the precedent these other
`self._` fields already set.

**Do NOT touch:** `AuthoritativeState` (`src/core/state.py`) — no new field is added there. Do not
confuse this with the existing `pending_information_responses`/`pending_self_model_information_events`
fields on `AuthoritativeState` (state.py:1147-1148) — those ARE durable, scenario-authored,
world-compile-time data (populated by `src/worldbuilding/compiler.py`, consumed once by
`src/cognition/self_model_phase.py`), a different mechanism with different origin and lifecycle;
this ticket's queue is purely a same-process cross-tick relay, not scenario content.

**Verify:** covered indirectly by Step 5's integration test (the queue has no directly-testable
public surface by itself — it's private `Kernel` bookkeeping).

### Step 4 — Extend the mid-tick death detection to also queue a grief trigger and emit `grief_urgency_triggered`

**Files:** `src/observability/event_extractor.py`, `src/observability/events.py`

**Change (events.py):** Verified the exact event-class pattern to copy:
`LegendaryArrivalEvent`/`KnownTraitorSpottedEvent`/`OldDebtCollectedEvent`
(`src/observability/events.py:357-431`) — each is a `SimulationEvent` subclass with fixed
`event_type`/`event_category="social"`/`severity`/`source_system`, plus a `__init__` that
auto-generates `message` if not supplied. Add two new classes following this exact shape:
```python
GRIEF_URGENCY_TRIGGERED: str = "grief_urgency_triggered"
NEMESIS_RELATION_FORMED: str = "nemesis_relation_formed"

class GriefUrgencyTriggeredEvent(SimulationEvent):
    dead_ally_id: int = 0
    urgency: float = 0.0
    event_type: str = GRIEF_URGENCY_TRIGGERED
    event_category: EventCategory = "social"
    severity: EventSeverity = "INFO"
    source_system: str = "event_extractor"
    message: str = ""
    def __init__(self, **data): ...  # same auto-message pattern as LegendaryArrivalEvent

class NemesisRelationFormedEvent(SimulationEvent):
    antagonist_id: int = 0
    strength: float = 0.0
    event_type: str = NEMESIS_RELATION_FORMED
    event_category: EventCategory = "social"
    severity: EventSeverity = "INFO"
    source_system: str = "campaign_orchestrator"
    message: str = ""
    def __init__(self, **data): ...
```
`GriefUrgencyTriggeredEvent.source_system="event_extractor"` matches the mid-tick emission point
(Step 4 below); `NemesisRelationFormedEvent.source_system="campaign_orchestrator"` matches its
episode-boundary emission point (Step 6).

**Change (event_extractor.py):** Verified the exact hook: `if prior_ent.lifecycle.active and not
entity.lifecycle.active:` (event_extractor.py:483), inside the existing block that already appends
`CombatKillEvent` (495-498, gated) and the unconditional `hero_death_unrecorded` `SimulationEvent`
(505-515). Immediately after that existing block (still inside the same `if` at line 483), add: for
every OTHER live entity in `current_state.entities.values()` (the same `current_state`/`entity`
dict `EventExtractor.extract()` already receives as a parameter — verified via the call site
`EventExtractor.extract(prior_state, self._state, update, obs_mode)` at kernel.py:915, which passes
the full post-apply state), check `getattr(other.social, "trust_history", {}).get(eid, 0.0) >=
ALLY_TRUST_THRESHOLD` (importing `ALLY_TRUST_THRESHOLD` locally from
`src.domains.campaigns.grief_urgency`, matching grief_urgency.py:25's constant exactly — verified
`entity.social.trust_history` is the live field `SocialMemoryExporter.export()` already reads at
`src/domains/campaigns/social_memory.py:450`, so this is live, in-episode data, not something that
requires `CampaignState`). For each qualifying `other`: append
`GriefUrgencyTriggeredEvent(tick=tick, entity_id=other.id, dead_ally_id=eid, urgency=round(min(1.0,
trust * 0.8), 6), ...)` to the function's `events` list (same urgency formula as
`_advance_grief_urgencies()`, orchestrator.py:260, kept identical to avoid a second, drifting
formula), and separately return the raw `(other.id, eid, urgency)` triples so `_phase_observability`
can queue them (see next). Since `EventExtractor.extract()`'s existing return type
(`List[SimulationEvent]`) must not change (regression risk to its many callers/tests), do this via
a new sibling method `EventExtractor.detect_grief_triggers(prior_state, current_state) ->
list[tuple[int,int,float]]` that re-walks the same lifecycle-transition condition independently (a
second, bounded pass over `current_state.entities` — acceptable cost, same order as the existing
pass), called from `Kernel._phase_observability` right after the existing
`EventExtractor.extract(...)` call (kernel.py:915): its events get appended into `generated_events`
(so `grief_urgency_triggered` gets recorded via the existing `self._event_recorder.record(event)`
loop at kernel.py:987-988, and reaches SimQ scoring like any other event), and its raw triples get
appended to `self._pending_grief_triggers` (Step 3's new field).

**Other writers to `entity.social.trust_history`**: this step only *reads* `trust_history`, never
writes it — no collision risk. The write side (`SocialUpdate`/trust-history mutation systems) is
untouched by this ticket.

**Do NOT touch:** the existing `CombatKillEvent`/`hero_death_unrecorded` logic at
event_extractor.py:483-515 — only append after it, inside the same `if` block. Do not build a new
`WorldEventCategory.ENTITY_DEATH` `WorldEvent` producer (per investigation's explicit anti-drift
finding — `ENTITY_DEATH` stays unproduced; this step reuses the lifecycle-transition signal only).

**Verify:** `test_grief_urgency_triggered_event_shape` (test_plan.md AC2, new, in
`tests/unit/observability/test_events.py`); a new unit test for
`EventExtractor.detect_grief_triggers()` directly (assert it returns the correct `(griever_id,
dead_id, urgency)` triples given a prior/current state pair with a qualifying trust_history).

### Step 5 — Drain the queue in `_phase_resolution` and apply through `ApplyPath`

**Files:** `src/engine/kernel.py`

**Change:** Verified `_phase_resolution()` (kernel.py:576-680) builds `entity_updates: Dict[int,
EntityUpdate]` from `self._final_results` (586-625), then constructs `raw_update =
StateUpdate(entity_updates=entity_updates, ...)` (641-647) and calls
`AuthoritativeApplyPipeline.refine(self._state, raw_update, ...)` (649-654) — this is the single
point every per-entity `EntityUpdate` passes through before `ApplyPath`. Extract the drain logic
into a new private `Kernel` method, `_drain_pending_grief_triggers(self, entity_updates:
Dict[int, EntityUpdate]) -> Dict[int, EntityUpdate]`, so Step 5b's episode-teardown flush can reuse
the exact same drain-and-build logic instead of duplicating it (Step 5b depends on this
extraction). The helper: for each `(griever_id, dead_id, urgency)` in
`self._pending_grief_triggers`: build `modifier = GriefUrgencyModifier(entity_id=griever_id,
dead_ally_id=dead_id, episode=self._state.tick, urgency=urgency)` and call
`GriefUrgencyImporter.build_strategic_update(modifier)` (Step 2) to get a `StrategicUpdate`; wrap in
`EntityUpdate(entity_id=griever_id, strategic=update)`. Verified `EntityUpdate.merge()` exists
(`src/core/updates.py:677`) and is the established merge mechanism (used identically by
`AuthoritativeApplyPipeline` phases via `u.merge(...)`, e.g. `src/engine/pipeline.py:173,212,242,252,276`)
— use it: `entity_updates[griever_id] = entity_updates[griever_id].merge(new_eu) if griever_id in
entity_updates else new_eu`. Clear `self._pending_grief_triggers = []` before returning
`entity_updates`. In `_phase_resolution()`, immediately after line 625 (entity_updates populated
from final_results) and before line 641, replace the inline loop with a single call:
`entity_updates = self._drain_pending_grief_triggers(entity_updates)`. This makes the grief
`StrategicUpdate` flow through `AuthoritativeApplyPipeline.refine()` →
`StrategicPatch.apply()` (`src/engine/patches.py:415-455`, verified: merges
`concerns_add_or_update` into `entity.strategic.concerns` via `merge_dict()`, lines 421-429,445) —
the same authoritative route `src/engine/tactical.py:186-196` already uses for its own
`StrategicUpdate`. **Note on `GriefUrgencyModifier.episode`**: this field is meaningful at the
`CampaignState` layer (`src/domains/campaigns/state.py:57-69`, doc comment: "episode: int #
episode when grief was created" — and it's the field `_advance_grief_urgencies()` populates with a
real episode index, orchestrator.py:264) but `Kernel` has no concept of "episode" — it only has
`tick`. Use `episode=self._state.tick` here instead (verified `GriefUrgencyImporter.apply()` only
reads `modifier.dead_ally_id`, `.urgency`, and `.episode` for the `source=` string,
grief_urgency.py:57 — `.episode` is never read for anything requiring real episode-count semantics
in this call path) so the `source=` string stays informative, e.g. `f"ally_{dead_id}_died_tick{tick}"`
rather than reusing the episode-boundary wording verbatim; this is a cosmetic `source=` string
difference between the two trigger paths, acceptable since AC3 doesn't require identical `source=`
text, only identical concern kind/mechanism. **Non-blocking architecture-review finding — address
with a comment, not a rename:** add a one-line code comment at this
`GriefUrgencyModifier(episode=self._state.tick, ...)` construction site inside
`_drain_pending_grief_triggers()`, stating that this `episode=` value is a transient,
per-Kernel-run substitute used only to keep the `source=` string informative, and is **never**
persisted to `CampaignState.grief_urgencies` (that dict is written only by
`_advance_grief_urgencies()`, orchestrator.py:224-268, using a real episode index) — so a future
maintainer does not mistake this in-tick modifier for a real, persistable `GriefUrgencyModifier`
row. Because `_drain_pending_grief_triggers()` is shared with Step 5b, this one comment covers both
call sites.

**Other writers to `entity_updates` in this phase**: only `self._final_results`-derived writes
(kernel.py:619-625, one per entity from decision-system results) — this drain step runs strictly
after that loop completes and only adds/merges entries, never removes or overwrites an existing
key's non-strategic fields (via `.merge()`, which is additive per `StrategicUpdate.merge()`,
`src/core/updates.py:538-578`). No collision: `StrategicUpdate.merge()` concatenates
`concerns_add_or_update` lists rather than overwriting, so a decision system's own strategic update
for the same entity in the same tick is preserved alongside the grief concern.

**Do NOT touch:** `_phase_scheduling`/`_phase_collection`/`_phase_cleanup`/`_phase_advancement`/
`_phase_persistence` — only `_phase_resolution` and `__init__`/`_phase_observability` (Steps 3-4).
Do not move `_phase_observability` earlier in the phase order — this plan works within the existing
7-phase ordering per `docs/engine/kernel.md`, applying one tick later instead. Do not inline the
drain loop back into `_phase_resolution()` once it's extracted — `_drain_pending_grief_triggers()`
must stay a standalone method so Step 5b's teardown flush can call the identical logic.

**Verify:** `test_mid_episode_entity_death_triggers_grief_concern_via_apply_path` (test_plan.md AC3,
integration) — a scripted 2-tick scenario where an ally with sufficient `trust_history` dies at
tick N, then assert `ConcernState(kind=SOCIAL_THREAT)` appears in the griever's
`entity.strategic.concerns` at tick N+1 (not N), applied through the normal tick pipeline (assert
via `DirtySet`/dirty-entity tracking per the CLAUDE.md architecture-test requirement). Also
`test_mid_episode_death_does_not_duplicate_episode_boundary_grief` (test_plan.md, dedup guard) —
because the mid-episode concern uses `concern_id = f"grief_ally_{dead_ally_id}"` (identical id
formula to the episode-boundary path, grief_urgency.py:53), a later episode-boundary
`_advance_grief_urgencies()` call for the same death is naturally idempotent (StrategicPatch's
`merge_dict()` overwrites by id, patches.py:425-426) rather than double-injecting — verify this
explicitly.

### Step 5b — Drain a last-tick-queued trigger at episode teardown, before the Kernel is discarded

**Files:** `src/engine/kernel.py`, `src/engine/scenario_runtime.py`, `src/domains/campaigns/orchestrator.py`

**Change:** Architecture-review finding (this step exists specifically to close it): a death
detected by `event_extractor.py:483` during an episode's FINAL tick queues into
`self._pending_grief_triggers` (Step 3/4) but Step 5's drain only runs at the START of a
*subsequent* tick's `_phase_resolution()`. There is no tick N+1 within that `Kernel` run once
`ScenarioRuntimeService._run_loop()` (`src/engine/scenario_runtime.py:259-268`) exits — victory
condition met, `tick_limit` reached, or `abort()` — so the queued trigger would be silently lost
from that `Kernel` instance's perspective before `CampaignOrchestrator.run_episode()`
(`orchestrator.py:172-178`) discards it. Without this step, AC3's "within the same episode"
guarantee would silently fail for exactly this edge case: the death would still be picked up, but
only one episode LATER, via `_advance_grief_urgencies()`'s `NarrativeLedgerEntry` conversion
(orchestrator.py:224-268) feeding `CampaignState.grief_urgencies`, converted into a live concern
only at the *next* episode's `_build_initial_state()` call — not this episode's `final_state`.

Verified the exact commit mechanics required to fix this correctly — calling
`AuthoritativeApplyPipeline.refine()` alone (the reviewer's own suggested starting point) is
**not** sufficient: `refine()` (`src/engine/pipeline.py:41-53`) only computes a refined
`StateUpdate` through its phase sequence — it does not itself write new `EntityState` objects into
`state.entities` (confirmed: no `state.entities[` assignment anywhere in `pipeline.py`). The actual
per-entity commit happens in `ApplyPath.apply_generation()` (`src/engine/apply.py:189-243`), which
`Kernel._phase_advancement()` calls as a *second*, separate step after `_phase_resolution()`
(`kernel.py:714-734`): `self._state = ApplyPath.apply_generation(self._state, update,
next_tick=self._state.tick + 1, next_world_time=self._current_world_time,
cadence=self._profile.cadence, audit_mode=self._audit_mode,
audit_dirty_set=self._audit_dirty_set)` — this is what reconstructs `state.entities` via
`plan.entities_to_replace`/`ApplyPath._fast_replace_entity()` (apply.py:234-243) and reassigns
`self._state` to the new object. Both `refine()` and `apply_generation()` are required for a
queued `StrategicUpdate` to actually land in `entity.strategic.concerns`.

Add a new public `Kernel` method:
```python
def drain_pending_triggers_at_teardown(self) -> None:
    """One-shot resolution+apply flush for a death detected on this Kernel run's FINAL
    tick, which _phase_resolution never gets a tick N+1 to drain into before this Kernel
    instance is discarded at episode teardown (TCK-20260824-GRIEF-NEMESIS-REACHABILITY).

    Reuses _drain_pending_grief_triggers() (Step 5) and the same
    AuthoritativeApplyPipeline.refine() + ApplyPath.apply_generation() commit route as a
    normal tick's _phase_resolution/_phase_advancement pair, but does NOT run
    _phase_scheduling/_phase_collection/_phase_cleanup/_phase_observability/_phase_persistence
    and does NOT advance self._state.tick or world_time -- a narrow resolution+apply flush
    against the CURRENT (final) state, not a disguised extra tick. No-op if nothing queued.
    """
    if not self._pending_grief_triggers:
        return
    from src.core.updates import StateUpdate
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.engine.apply import ApplyPath

    entity_updates = self._drain_pending_grief_triggers({})
    raw_update = StateUpdate(entity_updates=entity_updates)
    refined_update = AuthoritativeApplyPipeline.refine(
        self._state, raw_update,
        cadence=self._profile.cadence,
        force_full_scan=self._force_full_scan,
    )
    self._state = ApplyPath.apply_generation(
        self._state,
        refined_update,
        next_tick=self._state.tick,             # do NOT advance tick -- same-episode flush
        next_world_time=self._state.world_time,  # do NOT advance world_time either
        cadence=self._profile.cadence,
        audit_mode=self._audit_mode,
        audit_dirty_set=self._audit_dirty_set,
    )
```
`_force_full_scan`, `_audit_mode`, `_audit_dirty_set` are confirmed existing `Kernel` `__slots__`
attributes already set in `__init__` (`kernel.py:47-48,81-84`) — no new instance state needed.
`next_tick=self._state.tick` (not `+1`, unlike `_phase_advancement`'s own call) and
`next_world_time=self._state.world_time` (**not** `self._current_world_time`, which holds a stale
"what the next tick's world_time will be" value computed during the tick that already ran —
`kernel.py:44,197,506` — using it here would silently advance world_time on top of a tick that
never happened) are what keep this a same-tick, same-world-time commit instead of an extra tick.

Wire the call into `ScenarioRuntimeService` (`src/engine/scenario_runtime.py`) as a new public
method:
```python
def flush_pending_grief_triggers(self) -> None:
    """Drain any Kernel-queued grief trigger detected on the episode's final tick, before
    final_state is read. No-op if the kernel was never built or nothing is queued."""
    if self._kernel is not None:
        self._kernel.drain_pending_triggers_at_teardown()
```
(a method, not a new `__slots__` attribute — no `ScenarioRuntimeService.__slots__` change needed).
Then in `CampaignOrchestrator.run_episode()` (`orchestrator.py:172-178`), insert the call **after
`svc.start()` returns and before `final = svc.final_state` is captured** — this ordering is
load-bearing, not stylistic: `ScenarioRuntimeService.final_state` (`scenario_runtime.py:245-255`)
returns `self._kernel.state` *by reference, evaluated at read time*, and
`ApplyPath.apply_generation()` reassigns `self._kernel._state` to a **new** object — so if `final`
were captured before the flush, the local variable in `run_episode()` would keep pointing at the
stale pre-flush state object and the fix would silently do nothing from the caller's perspective:
```python
svc = ScenarioRuntimeService(spec, initial_state=initial_state)
try:
    svc.start()
    episode_run_id = svc.run_id           # Step 1a — order vs. the next line doesn't matter
    svc.flush_pending_grief_triggers()    # Step 5b — NEW, must precede final_state capture
    final = svc.final_state  # AuthoritativeState after terminal tick
    completed_tick = svc.tick
finally:
    svc.abort()  # Shuts down kernel worker threads; idempotent.
```

**Other writers to `self._kernel._state`**: within one `Kernel` run, only `_phase_advancement()`
(kernel.py:726, the per-tick path) and this new teardown method ever reassign `self._state`. They
cannot race: the teardown method only runs once, after `ScenarioRuntimeService._run_loop()` has
already exited for good (no further `tick_once()` calls occur for this `Kernel` instance once
`svc.start()`/`svc.resume()` returns control to `run_episode()`), so there is no concurrent-writer
or ordering hazard to reconcile — the two writers are strictly sequenced by the caller, never
interleaved. `_phase_resolution()`/`refine()` do not write `self._state` directly (confirmed
above), so they are not a third writer either.

**Do NOT touch:** `_phase_scheduling`/`_phase_collection`/`_phase_cleanup`/`_phase_observability`/
`_phase_persistence` — the teardown method calls none of these phase methods and never calls
`tick_once()`, by design, per the ticket's explicit "not a disguised extra tick" requirement. Do
not call `_run_hard_law_checks()` from the teardown method either — it is invoked only by
`_phase_advancement` today (kernel.py:736), and this flush only ever adds
`concerns_add_or_update` entries (no combat/economy mutation), so the hard-law risk surface it
would guard is not exercised here; wiring it in would require designing a new invariant-check
contract for a non-tick context, which is out of scope for this ticket. Do not use
`self._current_world_time` for `next_world_time=` (see above — it holds a stale next-tick value).
Do not duplicate the drain-loop body inline in this method — it must call the shared
`_drain_pending_grief_triggers()` helper (Step 5) so the two call sites cannot drift. Do not call
this method from anywhere other than `ScenarioRuntimeService.flush_pending_grief_triggers()` /
`CampaignOrchestrator.run_episode()` — in particular, do not call it from `Kernel.shutdown()`
itself, since `shutdown()` (kernel.py:1076-1098) is also invoked by `abort()` *after* `final_state`
would already have been read in the intended call order above, which would defeat the fix the same
way a wrong ordering would.

**Verify:** new integration test `test_death_on_final_tick_still_applies_grief_concern_same_episode`
(new, alongside `test_mid_episode_entity_death_triggers_grief_concern_via_apply_path`, same file
Step 5's test lands in) — script a scenario where the qualifying ally death is detected on the
episode's LAST tick (the tick after which the victory condition fires and `_run_loop()` exits with
no tick N+1 remaining), run it through `ScenarioRuntimeService.start()` (or
`CampaignOrchestrator.run_episode()` if the fixture shape supports scripting a final-tick death
that way — confirm the concrete harness via `test-scoper` at Test phase, consistent with Step 1a's
precedent for this kind of detail; note `EntityCarryForward`, orchestrator.py:365-374, does not
surface `strategic.concerns`, so the assertion must read `entity.strategic.concerns` directly off
`svc.final_state`/`kernel.state`, the same level Step 5's own test already operates at), and assert
the griever's `ConcernState(kind=SOCIAL_THREAT)` for the dead ally is present in
`final_state.entities[griever_id].strategic.concerns` **in this same episode run** — not requiring
a second episode to observe it via the `CampaignState.grief_urgencies` episode-boundary fallback.
Also assert `kernel._pending_grief_triggers == []` afterward, confirming the queue was actually
drained and not merely ignored. New unit test
`test_kernel_drain_pending_triggers_at_teardown_noop_when_empty` (`tests/unit/engine/`, wherever
`Kernel` unit tests already live) asserting the teardown method is a true no-op — `self._state`
object identity unchanged, `AuthoritativeApplyPipeline.refine`/`ApplyPath.apply_generation` not
called (spy/mock) — when `self._pending_grief_triggers` is empty, guarding against the flush
becoming an unconditional extra state-rebuild on every episode. New unit test
`test_kernel_drain_pending_triggers_at_teardown_does_not_advance_tick_or_world_time` asserting
`self._state.tick` and `self._state.world_time` are unchanged after a non-empty drain — the direct
regression guard for this fix's explicit "not a disguised extra tick" requirement.

### Step 6 — Emit `nemesis_relation_formed` from the existing episode-boundary path

**Files:** `src/domains/campaigns/orchestrator.py`

**Change:** Verified `_advance_nemesis_relations()` (orchestrator.py:270-306) builds
`new_relations: Dict[str, NemesisRelation]` starting as a copy of `self._state.nemesis_relations`
(283), then adds/updates entries in a loop (292-304), finally assigning `self._state.nemesis_relations
= new_relations` (306). Before that final assignment, compute `newly_formed = {k: v for k, v in
new_relations.items() if k not in self._state.nemesis_relations}` (must be computed before the
reassignment, using the *old* `self._state.nemesis_relations` as the base for comparison — reuse
the same dict reference already captured at line 283 into a local before it's overwritten). For each
`newly_formed` relation, call `self._emit_nemesis_event(relation, tick)` — a new small private
method mirroring `_emit_chronicle_events()`'s existing `if self._event_recorder is None: return`
no-op guard (orchestrator.py:308-336) — emitting `NemesisRelationFormedEvent(tick=tick,
entity_id=relation.protagonist_id, antagonist_id=relation.antagonist_id,
strength=relation.strength, source_system="campaign_orchestrator")` (Step 4's new event class).
Similarly, in `_advance_grief_urgencies()` (orchestrator.py:224-268), for each newly-created (not
merely decayed) `GriefUrgencyModifier` in the `entry` loop (250-266), also emit
`GriefUrgencyTriggeredEvent(tick=<the completed episode's tick>, entity_id=eid, dead_ally_id=dead_id,
urgency=urgency, source_system="campaign_orchestrator")` — giving the pre-existing episode-boundary
path the same event visibility the new mid-episode path gets in Step 4, so AC2's "queryable by a
SimQ pillar" holds for both trigger mechanisms, not just the new one.

**Other writers to `self._state.nemesis_relations`/`self._state.grief_urgencies`**: only this same
method (`_advance_nemesis_relations`/`_advance_grief_urgencies`) writes these `CampaignState`
fields — confirmed by `grep -rn "nemesis_relations\s*=\|grief_urgencies\s*=" src/domains/campaigns/`
— no concurrent writer to reconcile.

**Do NOT touch:** the relation-formation/decay logic itself (270-306, 224-268) — only add event
emission calls; do not change `strength`/`urgency` computation or the `NEMESIS_EPISODE_COUNT`/
`ALLY_TRUST_THRESHOLD` thresholds.

**Verify:** extend `tests/unit/domains/campaigns/test_grief_urgency.py` (or
`test_campaign_orchestrator.py`) with a spy-`EventRecorder` test asserting `nemesis_relation_formed`
fires exactly once per newly-formed relation (not on every episode a pre-existing relation is
merely refreshed) and `grief_urgency_triggered` fires only for new-death-triggered modifiers, not
for every decayed-but-still-positive existing modifier.

### Step 7 — Wire `SocialScorer` to score both new event types

**Files:** `src/simulation_quality/scorers/social.py`, `config/simulation_quality/scoring_weights.yaml`

**Change:** Verified `SocialScorer.EVENT_TYPES` (social.py:19-31) is a plain tuple matched by `if et
==` branches in `score()` (38-117), and each branch reads a weight via `self.weights["<key>"]`
(`ScoringWeights.__getitem__`, confirmed pattern at every existing branch, e.g. line 70/74/77/80).
Add `"grief_urgency_triggered"` and `"nemesis_relation_formed"` to `EVENT_TYPES`, and two new `if
et ==` branches following the exact shape of the existing `social_memory_created` branch (114-115):
```python
if et == "grief_urgency_triggered":
    return _rec(self.weights["grief_urgency_triggered"], "grief urgency injected from ally death", ("grief_urgency",))
if et == "nemesis_relation_formed":
    return _rec(self.weights["nemesis_relation_formed"], "nemesis relation formed from repeated antagonism", ("nemesis_relation",))
```
Add matching weight keys under the `SOCIAL:` section of `config/simulation_quality/scoring_weights.yaml`
(verified section exists at scoring_weights.yaml:107, alongside `cooperation_active: 4.0`,
`group_forming: 2.0`, `contract_honored: 3.0` — add `grief_urgency_triggered: <value>` and
`nemesis_relation_formed: <value>` at comparable magnitude, e.g. 3.0 each, matching
`contract_honored`'s tier as a "meaningful relationship-state event," not a `cooperation_active`-tier
routine one).

**Other writers to `scoring_weights.yaml`'s `SOCIAL:` section**: none found via `grep -rn
"SOCIAL:" config/simulation_quality/scoring_weights.yaml` (single occurrence) — this is a static
config file, not runtime-written; no concurrency concern.

**Do NOT touch:** `NarrativeScorer`/`narrative.py` (per Decision 2) or any other pillar's
`EVENT_TYPES`/weight section.

**Verify:** `test_social_scorer_scores_grief_urgency_triggered`/
`test_social_scorer_scores_nemesis_relation_formed` (test_plan.md AC2, extend
`tests/simulation_quality/test_social_scorer.py`) — assert a `ScoreRecord` with `pillar=SOCIAL` and
the correct `delta`/`tags` for each event_type.

### Step 8 — New campaign-aware SimQ profile and `calibrate_simq.py` branch

**Files:** `config/simulation_quality/profiles/campaign_life_arc.yaml` (new),
`tools/calibrate_simq.py`, `tests/simulation_quality/fixtures/grade_anchors.json`,
`config/simulation_quality/corpus_registry.yaml` (regenerated, not hand-edited)

**Change:** Create `config/simulation_quality/profiles/campaign_life_arc.yaml`:
```yaml
# TCK-20260824-GRIEF-NEMESIS-REACHABILITY -- campaign-aware SimQ profile. campaign_episodes
# selects the new _run_campaign_engine() branch in tools/calibrate_simq.py instead of the
# single-episode _run_engine() Kernel.tick_once() loop.
campaign_episodes: 3
feature_flags:
  ENABLE_LIFE_ARC_CAMPAIGNS: "ON"
```
In `tools/calibrate_simq.py`, add `_load_profile_campaign_episodes(profile: str) -> int` mirroring
`_load_profile_feature_flags()` (lines 51-..., same YAML-open/`.get("campaign_episodes", 0)`
pattern). Add `_run_campaign_engine(name, seed, ticks, episodes, entity_count=10, extra_flags=None,
cal_dir=None) -> tuple[str, float, str]`, parallel to `_run_engine()` (164-338), that: builds a
`CampaignManifest(id=name, episodes=[SimulationScenarioDefinition(id=f"{name}_ep{i}",
world_composition="frontier_living_world", perspective="hero_guild_perspective",
victory_conditions=[{"kind": "tick_limit", "value": ticks}]) for i in range(episodes)],
base_seed=seed)` — the exact `world_composition`/`perspective`/`victory_conditions` construction
verified working at `tests/integration/scenarios/test_campaign_runtime.py:34-45`'s `_make_spec()`
helper; constructs one `EventRecorder(run_dir=<new campaign run_dir>, max_events=5000, enabled=True)`
(same constructor signature `Kernel.__init__` uses at kernel.py:262-267) and a
`CampaignOrchestrator(manifest, event_recorder=campaign_recorder)`; calls `.run_episode()` `episodes`
times, capturing each `EpisodeSummary.run_id` (Step 1a); after all episodes, for each captured
`run_id`, reads `data/runs/{run_id}/simulation_events.jsonl` (if present) and appends its lines onto
`campaign_recorder`'s own JSONL file so `main()`'s existing `_replay_jsonl_through_hub(run_dir, hub)`
(calibrate_simq.py:341-365) sees every episode's mid-tick events (including
`grief_urgency_triggered`) plus the campaign-level events (`nemesis_relation_formed`,
`chronicle_entry_created`) in one file; returns `(campaign_run_dir, elapsed, campaign_run_id)`
matching `_run_engine()`'s contract exactly so `main()` needs only:
```python
episodes = _load_profile_campaign_episodes(profile)
if episodes > 0:
    run_dir, elapsed, run_id = _run_campaign_engine(name, seed, ticks, episodes, entities, extra_flags, cal_dir)
else:
    run_dir, elapsed, run_id = _run_engine(name, seed, ticks, entities, extra_flags, cal_dir)
```
inserted at `main()`'s existing call site to `_run_engine()`.

**Corpus registry**: per the investigation's explicit anti-drift note, `config/simulation_quality/corpus_registry.yaml`
is machine-generated by `tools/generate_corpus_registry.py` from
`tests/simulation_quality/fixtures/grade_anchors.json` and must never be hand-edited. Add a new
entry to `grade_anchors.json` for a `campaign_life_arc_seed<seed>_<ticks>t` run_key (matching the
existing entries' shape — read a sibling entry, e.g. for `lifecycle_full_coverage_world`, to copy
its exact field set before adding), then run `make simq-corpus-registry` (or
`python3 tools/generate_corpus_registry.py`) to regenerate `corpus_registry.yaml`. Stage the
regenerated file, never a manual edit.

**Other writers to `data/runs/`**: every `Kernel` instance writes to its own `data/runs/{run_id}/`
directory (kernel.py:222-227) — no collision, since each episode gets its own `run_id`
(`f"run_{int(time.time())}_{suffix}"`, kernel.py generation pattern) and the campaign-level
`EventRecorder` writes to yet another, separate `run_dir`. No shared-file write race.

**Do NOT touch:** `config/simulation_quality/corpus_registry.yaml` directly; any other profile YAML
under `config/simulation_quality/profiles/`; `_run_engine()`'s own body (only add a new sibling
function and a 4-line branch in `main()`).

**Verify:** `test_calibrate_simq_campaign_profile_runs_multiple_episodes` (test_plan.md AC1,
integration, new `tests/integration/tools/test_calibrate_simq_campaign_mode.py`) — asserts
`_run_campaign_engine()` calls `CampaignOrchestrator.run_episode()` at least twice (2+ episode
manifest) and produces a non-empty merged `simulation_events.jsonl` containing at least one
`chronicle_entry_created` event (proving the campaign-level recorder path works end-to-end);
`tests/tools/test_evaluate_simq_scenario_scope.py` must stay green after the corpus registry
regeneration.

### Step 9 — Docs and parity ledger updates

**Files:** `docs/parity_ledger/social_narrative.yaml`, `docs/mechanics/04_strategic_cognition.md`

**Change:** Update **SOC-231** (verified current text at social_narrative.yaml:2884-2894 — scoped to
"At the start of each episode, GriefUrgencyImporter.apply() injects..."): extend `text` to also
describe the new mid-episode path (`GriefUrgencyImporter.build_strategic_update()`, applied one
tick after detection via `Kernel._phase_resolution`/`StrategicPatch`, `event_extractor.py:483`
detection), and add/update `v2_evidence` to cite `src/engine/kernel.py::_phase_resolution` and
`src/observability/event_extractor.py::EventExtractor.detect_grief_triggers`. Keep `status:
verified`, `priority: P1` (unchanged — no P0 gate). **SOC-232** (social_narrative.yaml:2910-2920):
add a short note that `NemesisRelationImporter.build_strategic_update()` now exists for future
mid-episode use but is not yet wired to a live trigger (nemesis formation remains episode-boundary-
only, as explained in Step 2) — do not overstate current behavior. Add a new subsection to
`docs/mechanics/04_strategic_cognition.md` §3 "Strategic Memory: Leads & Blockers" (existing anchor
at line 86, verified by reading the file directly) documenting: the two trigger mechanisms now
coexist (episode-boundary via `_build_initial_state()`, direct `EntityState` return; mid-episode via
`event_extractor.py:483` detection → `Kernel._pending_grief_triggers` → `StrategicUpdate` →
`StrategicPatch`/`ApplyPath`, applied one tick after detection, still within the same episode —
except for a death detected on the episode's LAST tick, which Step 5b's
`Kernel.drain_pending_triggers_at_teardown()` applies immediately at episode teardown instead of
waiting for a tick N+1 that never comes, still within the same episode and still through the same
`ApplyPath`/`StrategicPatch` route); why same-tick application isn't possible in the general case
(`_phase_observability` runs after that tick's `ApplyPath`, per `docs/engine/kernel.md`'s 7-phase
ordering); and that nemesis relations remain episode-boundary-only by design (cross-episode
antagonism count).

**Do NOT touch:** `docs/engine/contracts/rpg_refinement_pillars.md` (explicitly out of scope per the
ticket) or any other parity ledger file (`strategic_cognition.yaml`'s STRAT-143/144, SOC-066 — all
confirmed unrelated legacy `check_nemesis_promotion()` entries, per investigation).

**Verify:** no automated test; verified by the Verify-phase parity-updater/doc-updater review per
CLAUDE.md's Authoritative Mechanics Rule.

## Scope Guards

- Do not touch `check_nemesis_promotion()`/`tick_place_attachment()` in
  `src/systems/social_systems/memory.py` — unrelated legacy grudge-threshold mechanism, tracked
  separately as `TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`.
- Do not touch `docs/parity_ledger/strategic_cognition.yaml`'s STRAT-143/STRAT-144 or
  `social_narrative.yaml`'s SOC-066 — confirmed unrelated to `CampaignState.nemesis_relations`.
- Do not resolve or edit the "Nemesis System overriding AI scoring" divergence in
  `docs/engine/contracts/rpg_refinement_pillars.md:57` — explicitly out of scope per the ticket.
- Do not build a `WorldEventCategory.ENTITY_DEATH` `WorldEvent` producer anywhere in `src/engine/`
  — the mid-episode trigger is built entirely on the already-firing `event_extractor.py:483`
  lifecycle-transition signal. This also means `src/domains/world_emergence/*` and its
  `QuestOpportunityGenerator.from_threat_signal()` consumer stay untouched and must not start
  receiving new `ENTITY_DEATH` events as a side effect.
- Do not add a durable field to `AuthoritativeState` (`src/core/state.py`) for the pending-trigger
  queue — it is `Kernel`-instance-level ephemeral bookkeeping (Step 3), not simulation state.
- Do not widen the `orchestrator.py:172` `event_recorder=` fix to any other
  `ScenarioRuntimeService(...)` construction site project-wide.
- Do not hand-edit `config/simulation_quality/corpus_registry.yaml` — regenerate via
  `tools/generate_corpus_registry.py` / `make simq-corpus-registry` from an updated
  `grade_anchors.json`.
- Do not change `_build_initial_state()`'s existing direct-`EntityState`-return contract or its two
  call sites (orchestrator.py:567-571, 576-579) — they keep calling `.apply()` exactly as today.
- Do not wire `NemesisRelationImporter.build_strategic_update()` (Step 2) into any live mid-episode
  call site — nemesis formation requires cross-episode data unavailable within one episode; this is
  a deliberate, ticket-consistent scope boundary, not an oversight.
- Do not modify `src/domains/optimization/degradation.py`'s `should_skip_phase()` — reusing the
  `ENABLE_LIFE_ARC_CAMPAIGNS` flag name in the new SimQ profile does not require touching this file.
- Do not move `Kernel._phase_observability` earlier in the 7-phase order, and do not attempt
  same-tick application of the mid-episode grief `StrategicUpdate` — for a death detected on any
  tick *other than* the episode's last one, it is applied one tick after detection via Step 5's
  normal `_phase_resolution` drain, which still satisfies AC3's "within the same episode" wording.
  For a death detected on the episode's LAST tick specifically, Step 5b's teardown flush applies it
  without waiting for a tick N+1 that will never come — see Step 5b; this is a narrow,
  edge-case-only exception to "applied one tick later," not a general same-tick mechanism, and it
  still does not run a full extra tick (no scheduling/collection/cleanup/observability/persistence
  phases — see Step 5b's own Do NOT touch list).
- Do not call `Kernel.drain_pending_triggers_at_teardown()` (Step 5b) from anywhere except
  `ScenarioRuntimeService.flush_pending_grief_triggers()`, and do not call
  `flush_pending_grief_triggers()` from anywhere except `CampaignOrchestrator.run_episode()`,
  positioned strictly after `svc.start()` and strictly before `final = svc.final_state` is
  captured — see Step 5b's ordering rationale (`final_state` returns a live-at-read-time reference
  that the flush reassigns).

## Dependency Map

- Step 1a (run_id plumbing) — independent; needed before Step 8 (campaign runner needs per-episode
  run_id to merge JSONL).
- Step 1b (event_recorder wiring) — independent of 1a; needed before Step 6's events can be
  observed via the campaign-level recorder.
- Step 2 (StrategicUpdate builders) — independent; a prerequisite for Step 5 (drain step calls
  `GriefUrgencyImporter.build_strategic_update()`).
- Step 3 (Kernel pending-queue field) — prerequisite for Step 4 (populates it) and Step 5 (drains
  it).
- Step 4 (detection + event) — depends on Step 3 (queue must exist) and Step 2's constant reuse
  (`ALLY_TRUST_THRESHOLD` import) — does not depend on Step 2's `build_strategic_update()` itself.
- Step 5 (drain + apply) — depends on Step 2 (builder), Step 3 (queue), and Step 4 (queue
  population).
- Step 5b (episode-teardown drain) — depends on Step 3 (queue must exist), Step 4 (queue
  population), and Step 5 (the shared `_drain_pending_grief_triggers()` helper Step 5 extracts —
  Step 5b calls it directly rather than duplicating it, so Step 5 must land first). Also depends on
  Step 1a only in the sense that both edit the same `run_episode()` try-block in `orchestrator.py`
  (Step 1a adds `episode_run_id = svc.run_id`, Step 5b adds `svc.flush_pending_grief_triggers()`);
  the two insertions are order-independent relative to each other but both must land before `final
  = svc.final_state`. Not required for Step 6/7/8 to function — Step 5b only closes the last-tick
  edge case, it does not change the event/scoring/entry-point machinery those steps add.
- Step 6 (episode-boundary event emission) — depends on Step 1b (event_recorder wiring must be in
  place for `CampaignOrchestrator`-level events to be captured) and the new event classes from Step
  4's events.py change.
- Step 7 (SimQ scorer wiring) — depends on Step 4 and Step 6 (event types must exist first).
- Step 8 (SimQ campaign entry point) — depends on Step 1a (run_id), Step 1b, and benefits from Steps
  4-7 being in place to have something meaningful to score, but is mechanically independent of them
  (could be implemented and tested with only existing event types).
- Step 9 (docs/parity) — last; depends on all behavior-changing steps (2, 4, 5, 5b, 6) being final.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `CampaignOrchestrator.run_episode()` reachable via a real production entry point | Steps 1a, 8 | `test_calibrate_simq_campaign_profile_runs_multiple_episodes` |
| AC2 — new event_type(s) emitted via `SimulationEvent`, queryable by a SimQ pillar | Steps 4, 6, 7 | `test_grief_urgency_triggered_event_shape`, `test_social_scorer_scores_grief_urgency_triggered`, `test_social_scorer_scores_nemesis_relation_formed` |
| AC3 — in-episode `entity_death` causes grief-urgency concern injection within the same episode via an authoritative-pipeline-compliant path (including a death on the episode's LAST tick) | Steps 2, 3, 4, 5, 5b | `test_grief_urgency_importer_returns_strategic_update`, `test_mid_episode_entity_death_triggers_grief_concern_via_apply_path`, `test_mid_episode_death_does_not_duplicate_episode_boundary_grief`, `test_death_on_final_tick_still_applies_grief_concern_same_episode`, `test_kernel_drain_pending_triggers_at_teardown_noop_when_empty`, `test_kernel_drain_pending_triggers_at_teardown_does_not_advance_tick_or_world_time` |

## Anti-Drift Notes

- The investigation's claim that the `orchestrator.py:172` event_recorder gap blocks mid-episode
  event observability is corrected in this plan (see Decisions section) — verified by reading
  `kernel.py:262,987-988` that each episode's own Kernel-internal `EventRecorder` already records
  every `EventExtractor`-generated event unconditionally. The fix is still made (Step 1b) because
  it is a real, separate gap (3 scenario-lifecycle events silently dropped), but the implementer
  must not assume it is a blocking prerequisite for Step 4/5's grief trigger to be observable.
- `ENTITY_DEATH` `WorldEventCategory` stays unproduced — confirmed by investigation via grep across
  `src/engine/economy.py`, `src/engine/military_conflict.py`, `src/engine/world_dynamics.py`. Any
  temptation to "just wire the WorldEvent producer since it's already defined" must be resisted —
  it activates a dormant `QuestOpportunityGenerator.from_threat_signal()` consumer as an unscoped
  side effect.
- `entity.social.nemesis_ids`/`check_nemesis_promotion()` (legacy grudge mechanism,
  `src/systems/social_systems/memory.py`) and `CampaignState.nemesis_relations`/`NemesisRelation`
  (this ticket's subject) share only the word "nemesis" — confirmed via code reading, different
  data model, different file, different trigger condition. Never conflate them.
- `_build_initial_state()`'s pre-`Kernel` direct-`EntityState`-return contract
  (orchestrator.py:483-618) has no `ApplyPath` to go through at that point in construction (it is
  building a brand-new `AuthoritativeState` from scratch) and must not be changed — only the new
  mid-episode call site (Step 5, inside a live `Kernel` tick) uses the `StrategicUpdate`-returning
  builder.
- The mid-episode grief `StrategicUpdate` is applied on the tick *after* detection, not the same
  tick, for every death **except one detected on the episode's LAST tick** — this is a structural
  consequence of `_phase_observability` running after that tick's `ApplyPath` (verified via
  `kernel.py:344-427`'s phase ordering), not an implementation shortcut. AC3 says "within the same
  episode," which this satisfies; it does not say "within the same tick." For the last-tick case,
  there is no tick N+1 to apply on — Step 5b's `Kernel.drain_pending_triggers_at_teardown()` closes
  that gap by applying at episode teardown instead (see below); it is the one case where "one tick
  later" is not what happens, because a tick later would mean a different episode.
- **Resolved architecture-review finding (previously a silent gap):** a death detected on an
  episode's FINAL tick has no tick N+1 within that `Kernel` run to drain
  `self._pending_grief_triggers` into before the `Kernel`/`ScenarioRuntimeService` instance is
  discarded at episode teardown. Left unhandled, this would make AC3's "within the same episode"
  guarantee silently fail for exactly this edge case — the death would still be picked up, but only
  one episode LATER via `_advance_grief_urgencies()`'s `NarrativeLedgerEntry` conversion
  (orchestrator.py:224-268) feeding `CampaignState.grief_urgencies`, converted into a live concern
  only at the *next* episode's `_build_initial_state()`, not this episode's `final_state`. Step 5b
  closes this for real (not by softening AC3's wording) with a genuine episode-teardown drain:
  `Kernel.drain_pending_triggers_at_teardown()`, wired into
  `ScenarioRuntimeService.flush_pending_grief_triggers()` and called from
  `CampaignOrchestrator.run_episode()` after `svc.start()` and before `final = svc.final_state` is
  captured. It reuses the same `AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation()`
  commit route a normal tick uses (verified `refine()` alone does not write `state.entities` —
  `apply_generation()` is the step that actually does, `src/engine/apply.py:189-243`) without
  running a full extra tick (no scheduling/collection/cleanup/observability/persistence phases, and
  `self._state.tick`/`world_time` are held constant — see Step 5b). This is now covered by
  `test_death_on_final_tick_still_applies_grief_concern_same_episode` and two supporting unit tests
  — not silently deferred. One accepted, narrower limitation remains and is intentionally
  out-of-scope for this ticket: the teardown flush does not call `_phase_persistence`, so no replay
  `TICK_END` trace event is written for it — acceptable because AC3 only requires `final_state`/
  carry-forward data to reflect the concern (which it does), not full replay-determinism parity for
  this one-shot edge-case event; a future replay-fidelity ticket could revisit this if it becomes a
  problem.
- `EpisodeSummary`'s new `run_id` field must use `.get("run_id", "")` in `from_dict()` so any
  previously-serialized `EpisodeSummary` records (without the field) still round-trip without a
  `KeyError`.

## Deviations

Steps 1a, 1b, 2, 3, 4, 5, 5b, 6, 7, and 8's `calibrate_simq.py`/profile-YAML portion were all
implemented exactly as specified — verified line-for-line against this plan during Finalize
(function names, call-site ordering, `.get("run_id", "")` default, `next_tick=self._state.tick`/
`next_world_time=self._state.world_time` non-advancement, the shared
`_drain_pending_grief_triggers()` helper used by both Step 5 and 5b, event class shapes, scorer
branches, and weight keys all match). No deviation on any of those.

**Step 8's "Corpus registry" subsection was intentionally NOT executed**, and this is a deviation
from the plan's literal text. The plan instructed adding a `campaign_life_arc_seed<seed>_<ticks>t`
entry to `tests/simulation_quality/fixtures/grade_anchors.json` and regenerating
`corpus_registry.yaml`. Verified live during Finalize
(`tools/evaluate_simq.py::_resolve_world_name("campaign_life_arc")`) that this fails with
`ValueError: Cannot resolve a world directory for profile 'campaign_life_arc' — no prefix of it
matches a directory under data/worlds/`. `tools/generate_corpus_registry.py::generate()` calls
`_resolve_world_name()` for every anchored run_key unconditionally, so adding this entry would not
merely fail to produce a new registry row — it would raise and prevent regeneration of the *entire*
`corpus_registry.yaml` file, breaking every existing entry's build (confirmed via
`tests/tools/test_corpus_registry.py::test_corpus_registry_covers_every_anchored_run_key` and
`::test_corpus_registry_world_names_resolve_to_real_directories`, which assert every anchored
run_key resolves to one real `data/worlds/{name}/` directory). The root cause is a structural
mismatch the plan did not anticipate: `campaign_life_arc` is a multi-episode campaign profile whose
episodes each use `world_composition="frontier_living_world"` (Step 8's own manifest construction)
— it has no single backing `data/worlds/{profile_name}/` directory the way every other
`evaluate_simq.py`-style single-engine-run profile does, so the corpus registry's per-run_key
world-resolution model does not support this profile shape at all.

This step was confirmed not required for any of the ticket's 3 acceptance criteria:
`tests/integration/tools/test_calibrate_simq_campaign_mode.py` (AC1) calls
`_run_campaign_engine()`/`_load_profile_campaign_episodes()` directly with explicit args and never
reads `corpus_registry.yaml` or `grade_anchors.json`; `tests/tools/test_evaluate_simq_scenario_scope.py`
(listed in test_plan.md as relevant "if a new corpus profile/run_key is added") uses a hardcoded
`_KEYS` list, not the real registry, so it is unaffected either way. Skipping this sub-step is
therefore strictly better than executing it literally, which would have broken
`generate_corpus_registry.py`/`test_corpus_registry.py` for the whole corpus as an unscoped side
effect. `config/simulation_quality/corpus_registry.yaml` and `grade_anchors.json` are left
untouched by this ticket (verified via `git status` and a full `test_corpus_registry.py` pass at
Finalize). A future ticket adding real multi-episode-profile support to
`generate_corpus_registry.py`'s world-resolution logic could revisit wiring `campaign_life_arc` into
the registry; out of scope here.

**Post-Test-phase gate fix (2026-08-26): episode-boundary grief/nemesis emission moved off the
dedicated event subclasses.** The real scoped pytest run at Test phase found
`tests/architecture/test_phase18_import_boundaries.py::test_domains_do_not_import_observability_outside_pinned_exceptions`
and `::test_observability_domains_systems_import_allowlist` failing — two real regressions, not
pre-existing/environment noise. `CampaignOrchestrator._emit_grief_urgency_events()` and
`_emit_nemesis_event()` (`src/domains/campaigns/orchestrator.py`) had been implemented importing
`GriefUrgencyTriggeredEvent`/`NemesisRelationFormedEvent` directly from `src.observability.events`
— new domains → observability import call sites not in the test's `(file, lineno)`-exact
`_DOMAINS_OBSERVABILITY_PINNED` grandfather list, and never intended to be added to it (the list is
a hardening gate, not something to route around). Fixed by following the file's own already-pinned
`_emit_chronicle_events()` pattern: episode-boundary grief/nemesis events are now constructed as the
base `SimulationEvent` with `event_type="grief_urgency_triggered"`/`"nemesis_relation_formed"`,
`event_category="social"`, and the per-event fields (`dead_ally_id`/`urgency`,
`antagonist_id`/`strength`) carried in `payload={...}` instead of typed subclass fields. Rather than
adding two more local `from src.observability.events import SimulationEvent` imports (which would
each need their own new pinned-allowlist entry — exactly the kind of addition the ticket forbade),
all three emit methods (`_emit_chronicle_events`, `_emit_grief_urgency_events`, `_emit_nemesis_event`)
were consolidated to route through one new private helper, `_emit_domain_event()`, which holds the
single, sole `SimulationEvent` import site. The pre-existing pinned exception for
`orchestrator.py` was relocated in `_DOMAINS_OBSERVABILITY_PINNED` (and in
`docs/audits/D14_coupling_depth.md`'s Coupling Inventory) from its old line 319 to the new import's
line 418 — a like-for-like relocation of the same already-approved import statement (unavoidable
since the ticket's own earlier changes shifted the file's line numbers, and the pin is line-exact),
not a new grandfathered addition; the pinned-entry *count* for this file did not increase. The
`GriefUrgencyTriggeredEvent`/`NemesisRelationFormedEvent` subclasses in
`src/observability/events.py` were left untouched — `src/engine/kernel.py`'s mid-episode path (via
`EventExtractor.detect_grief_triggers()`) still legitimately constructs them, which is
engine/observability same-layer-adjacent and not a `domains` boundary violation, confirmed by
`tests/unit/observability/test_events.py`'s unchanged, still-passing subclass tests.
`docs/mechanics/04_strategic_cognition.md`'s existing "SimulationEvent" wording for both event
types (added by the earlier Document-Update phase) needed no correction — it already avoided
over-specifying the orchestrator.py call site's class — only two stale source-line citations
(`grief_urgency.py:27`/`:30` for `ALLY_TRUST_THRESHOLD`/`NEMESIS_EPISODE_COUNT`) were corrected.

Also at the same gate: `tests/architecture/test_phase18_import_boundaries.py::test_observability_domains_systems_import_allowlist`
failed because `EventExtractor.detect_grief_triggers()` (`src/observability/event_extractor.py`)
imported `ALLY_TRUST_THRESHOLD` from `src.domains.campaigns.grief_urgency` — a new `src.domains`
import not in `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS`. `ALLY_TRUST_THRESHOLD` is a bare `float`
constant that conceptually belongs to neither layer; it was relocated to a new neutral module,
`src/core/social_constants.py` (matching this codebase's existing `src/core/` naming convention —
no comparable cross-cutting-constants module already existed there to reuse), since `src/core/` is
already freely imported by both `src.domains` and `src.observability` without triggering this rule.
`grief_urgency.py` now imports (and thereby re-exports) `ALLY_TRUST_THRESHOLD` from
`src.core.social_constants` rather than defining it locally, so there is a single source of truth
and any other caller still importing it from `grief_urgency.py` keeps working. `event_extractor.py`
now imports it from `src.core.social_constants` directly. `NEMESIS_EPISODE_COUNT`/
`NEMESIS_INTERACTION_KINDS` were left in `grief_urgency.py` unmoved — `event_extractor.py` only
ever needed `ALLY_TRUST_THRESHOLD`, so moving the other two would have been unscoped.

Two pre-existing unit tests broke as a direct, expected consequence of the `SimulationEvent`+
`payload` shape change (asserting `.dead_ally_id`/`.antagonist_id` as top-level attributes, which no
longer exist on the base class) and were updated in the same pass:
`tests/unit/domains/campaigns/test_grief_urgency.py::test_advance_grief_urgencies_emits_event_only_for_newly_created`
and `::test_advance_nemesis_relations_emits_event_only_once_per_new_relation` now assert
`event_category == "social"` and read the two fields via `.payload["dead_ally_id"]`/
`.payload["antagonist_id"]` instead. The two missing SocialScorer tests required by this plan's
Step 7 / test_plan.md AC2 (`test_social_scorer_scores_grief_urgency_triggered`,
`test_social_scorer_scores_nemesis_relation_formed`) were also added to
`tests/simulation_quality/test_social_scorer.py` in this pass, asserting `pillar=PillarId.SOCIAL`
and the correct `delta`/`tags` per event type — this had been an outstanding gap from the earlier
implementer pass, not a new deviation from this plan's own content.

Final re-run of the Test phase's exact scoped pytest command
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest -q -m "not slow"` over
the full listed path set): both architecture-boundary tests and both new SocialScorer tests pass.
Of the originally-reported 3 unrelated failures, all 3 reproduce identically
(`tests/tools/test_entity_event_ledger.py::test_entity_ledger_covers_every_entity_update_field` —
unrelated `cognition_bundle_set` field-coverage drift; `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`
— `docs/REGISTRY.yaml` staleness against this ticket's own `docs/mechanics/04_strategic_cognition.md`
edits, a Finalize-phase `make docs-registry`/registry-regeneration responsibility, not an
implementer-phase one; `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
— the documented baseline-drift pattern, 1331 vs. the test's hardcoded 1332, from an unrelated
concurrent ticket's parity-ledger `test_path` change). A 4th, previously-unseen failure,
`tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_reproducible_byte_identical_direct_call`,
appeared only inside the ~8-minute full-suite run and passed cleanly in isolated re-runs — confirmed
as the documented shared-worktree `agent-monitoring/tools.jsonl` concurrent-write race (this
session's own hook-driven writes landing mid-test), not a code regression.
