# Investigation — TCK-20260629-SIMQ-EMIT-NARRATIVE

**Ticket:** TCK-20260629-SIMQ-EMIT-NARRATIVE  
**Date:** 2026-06-30  
**Investigator role:** Investigator (seq 2)

---

## Current Behavior (file:line refs)

### NarrativeLedger — chronicle_entry_created gap

`src/domains/campaigns/narrative_ledger.py` — `NarrativeLedger.record()` (line 43)
appends a `NarrativeLedgerEntry` to `self._entries` in-memory only. It has no
`event_recorder` parameter and no event bus call. `to_jsonl()` (line 88) writes to disk
in append mode. Neither method has any observability hook.

`NarrativeLedger.__init__()` (line 38) takes only `entries: Optional[List]` — no injected
recorder. The class docstring (line 23) and `record()` docstring (line 43) explicitly note
it does not mutate `CampaignState.narrative_ledger` directly.

The `NarrativeScorer` docstring (line 11–17 of
`src/simulation_quality/scorers/narrative.py`) documents the gap: "chronicle_entry_created
events emitted as disk JSONL only (not event bus) are a known gap."

### WorldEmergencePhase — no narrative event emission

`src/domains/world_emergence/phase.py` — `WorldEmergencePhase.execute()` (line 29)
processes pressures, seeds, quest opportunities, and entity signals. It returns a
`WorldEmergenceResult` and a merged `StateUpdate`. Zero `world_emergence_event`,
`narrative_milestone`, or `scenario_objective_*` events are produced.

The pipeline wires this at `src/engine/pipeline.py:284` (phase name `"world_emergence"`)
using `WorldEmergencePhase.execute(state, u, recent_world_events)[0]` — only the
`StateUpdate` is consumed; `WorldEmergenceResult` is discarded.

`WorldEventCategory` enum (`src/domains/world_emergence/schema.py:15`) includes
`SOVEREIGNTY_SHIFT` (line 49), `FACTION_WAR_DECLARED` (line 38), `QUEST_COMPLETED`
(line 21). There is no `WORLD_EMERGENCE_THRESHOLD` or `NARRATIVE_MILESTONE` category.

### LifecycleSystem — no hero_death_unrecorded emission

`src/systems/lifecycle_systems/lifecycle.py` — `LifecycleSystem.resolve_lifecycle()`
(line 19) processes deaths by setting `is_permadeath_set`, `death_tick_set`, and
`death_reason_set` in `LifecycleUpdate`. It calls
`FactionInfluenceService.process_influence_shift()` and
`process_conquest_lifecycle()` (lines 90–94) but emits no `hero_death_unrecorded` event.
There is no check of whether the dying entity has `kind == "hero"` or whether a chronicle
entry was written for it this tick.

Entity kind `"hero"` is set in `src/core/builder.py:91` and is the default kind for the
builder. Boss kinds are `"world_boss"` and `"ancient_sentinel"` (used in
`event_extractor.py:481`). The hero kind pattern is `entity.kind == "hero"`.

### ScenarioRuntimeService — no scenario_objective_* emission

`src/engine/scenario_runtime.py` — `ScenarioRuntimeService._evaluate_after_tick()`
(line 266) evaluates `ObjectiveEvaluator.evaluate()` and the stall detector. When
`STALLED` state is set (line 307), no `scenario_stalled` event is emitted. When
`OBJECTIVE_MET` / `OBJECTIVE_FAILED` is set (line 287–288), no
`scenario_objective_completed` / `scenario_objective_progressed` event is emitted.

`ScenarioRuntimeService` has no `event_recorder` parameter and no reference to
`SimulationEvent`. The stall detector increments `_stall_counter` (line 306) and sets
state to `STALLED` (line 308) — state only, no side-channel emission.

### EventExtractor — no narrative events currently

`src/observability/event_extractor.py` — no occurrences of `world_emergence_event`,
`narrative_milestone`, `chronicle_entry_created`, `scenario_objective_progressed`,
`scenario_objective_completed`, `scenario_stalled`, or `hero_death_unrecorded`. The
`QuestEvent` type is already emitted at line 418 (quest project state diff), producing
`quest_event` with `status` field. The translation table
(`src/simulation_quality/quality_hub.py`) already remaps `quest_event` by payload status
to `quest_started` / `quest_completed` / `quest_failed` (TCK-20260629-SIMQ-EVENT-TRANSLATE,
confirmed done).

### Pipeline phase labels (PP numbers)

The ticket uses PP-23 for `world_emergence` and PP-33 for `lifecycle`. The actual pipeline
code uses string phase names (`"world_emergence"` at pipeline.py:284, `"lifecycle"` at
pipeline.py:326). There is no integer phase numbering in the codebase. PP-23/PP-33 are
ticket-level labels only; the actual code sites are:
- `"world_emergence"` phase: `pipeline.py:284`, delegate to `WorldEmergencePhase.execute()`
- `"quest_rewards"` phase: `pipeline.py:292`, delegate to `QuestRewardPhase.resolve()`
- `"lifecycle"` phase: `pipeline.py:326`, delegate to `LifecycleSystem.resolve_lifecycle()`

### WorldEmergenceResult — currently discarded in pipeline

`pipeline.py:284`: `WorldEmergencePhase.execute(state, u, recent_world_events)[0]` —
index `[0]` takes only the `StateUpdate`; the `WorldEmergenceResult` (index `[1]`) is
silently discarded. Emitting `world_emergence_event` requires either:
(a) EventExtractor consuming the result (requires passing it out of the pipeline), or
(b) WorldEmergencePhase itself appending `world_events_add` entries that EventExtractor
then reads.

Option (b) is the established pattern: `QuestOpportunityRewardSystem.enforce()` appends
`WorldEvent(category=WorldEventCategory.QUEST_COMPLETED)` to `world_events_add` at
`quest_opportunity_rewards.py:106–118` — EventExtractor already reads `world_events_add`
at `event_extractor.py:555`.

### Narrative milestone "first X" — no existing tracking

There is no kernel-level milestone tracker or run-level stateful set. The
`NarrativeScorer` has per-instance flags (`_quest_dormant_fired`, etc.) but these are
in the scoring layer, not the emission layer. Emitting `narrative_milestone` for "first
war declaration / first boss kill / first sovereignty transfer" requires either:
- A stateful set in `WorldEmergencePhase` (but it is a stateless `@staticmethod`)
- A run-level tracker injected into or alongside `WorldEmergencePhase`
- Attaching milestone flags to `AuthoritativeState`

The ticket notes war_declared events are already emitted by EventExtractor (line 562)
from `WorldEventCategory.FACTION_WAR_DECLARED`. `narrative_milestone` would require
detecting "first" occurrence, which needs run-level state that is not currently present
in either the phase or the extractor.

### ScenarioRuntimeService — no event_recorder parameter

`ScenarioRuntimeService.__init__()` (line 129) takes only `spec` and `initial_state`.
It constructs a `Kernel` via `_build_kernel()` (line 311) with no observability injection.
Emitting scenario_objective events requires either:
- Adding an `event_recorder` parameter to `ScenarioRuntimeService`
- Having `_evaluate_after_tick()` call a callback
- Detecting stall/objective state changes in EventExtractor from StateUpdate fields

There is no `scenario_stalled` or `scenario_objective_*` field in `StateUpdate` or
`AuthoritativeState` that EventExtractor could observe via state diff.

---

## Mechanics/Engine Constraints

Per `docs/simulation_quality/quality_scoring_contract.md` §5 NARRATIVE (confirmed at
lines 835–865):

- Pipeline sources for NARRATIVE: PP-23 (`world_emergence`), PP-24 (`quest_rewards`),
  PP-33 (`lifecycle`), PP-08 (`faction_decision`)
- `quest_started/completed/failed`: already covered via QuestEvent + translation layer
- `chronicle_entry_created`: NarrativeLedger gap — requires EventRecorder injection
- `world_emergence_event`: "threshold-triggered narrative event" — requires threshold
  detection logic in WorldEmergencePhase; no such threshold currently exists
- `narrative_milestone`: first war/boss kill/sovereignty — requires "first" detection
- `scenario_objective_progressed/completed/stalled`: ScenarioRuntimeService has the
  state machine but no emission hook

Engine contract (TOWN-147, TOWN-148 from pipeline.py:1–3): all mutations pass through
`refine()`. EventExtractor runs AFTER the pipeline, reading state diffs and update
fields. Adding emission hooks must not import from `src/simulation_quality/`.

Architecture law: `WorldEmergencePhase.execute()` is a `@staticmethod` — it has no
`__init__` and cannot carry stateful milestone trackers without a design change.

---

## Parity Ledger Overlap (IDs + status)

| Parity ID | Text summary | Status | Overlap |
|---|---|---|---|
| INFRA-247 | NarrativeScorer covers §5 NARRATIVE; chronicle_entry_created gap documented | `verified` / P1 | Direct — this ticket resolves the documented gap |
| SIMQ-CALIBRATED-001 | Calibration operational; "Full calibration requires remaining EMIT tickets (COGNITION, WORLD, ECONOMY, NARRATIVE)" | `verified` / P1 | Direct — this is one of the four remaining tickets listed |

INFRA-247 must be updated: its `divergence_note` field should be cleared or updated once
`chronicle_entry_created` is wired to the event bus. The `text` field documents the gap
explicitly and should be updated to reflect it is now resolved.

SIMQ-CALIBRATED-001 must be updated: append NARRATIVE pillar emit status to `v2_evidence`
and confirm non-zero NARRATIVE events from the new emission sites.

No other parity ledger files overlap directly (social_narrative.yaml entries SOC-* cover
social contracts and group behavior, not narrative event emission).

---

## Prior Work

**TCK-20260629-SIMQ-EVENT-TRANSLATE (DONE):** Quest translation confirmed working.
`quest_event` with `payload["status"]` remapped to `quest_started/completed/failed` in
`QualityHub._translate()`. This covers 3 of 10 NARRATIVE event types. The 7 remaining
require new emission sites.

**TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION (DONE):** Established the pattern of:
- EventExtractor reads `update.world_events_add` for faction-level events
- EventExtractor reads `update.faction_updates` for diplomatic events
- State-diff in entity loop for per-entity events
- Gap tests for architecture-blocked events (4 gap tests with `pytest.skip`)

**TCK-20260629-SIMQ-EMIT-ECONOMY (DONE):** Established pattern of reading
`intent_results` instead of `resource_transfers` (cleared before EventExtractor runs).
Key lesson: know which update fields survive pipeline phases.

**TCK-20260628-E43H-NARRATIVE-OBS / TCK-20260628-E-NARRATIVE-CONSEQUENCE (DONE):**
Prior narrative observability work; NarrativeLedger already has `to_jsonl()` for disk
output; no event bus wiring existed.

**TCK-20260619-E32D-NARRATIVE-LEDGER (DONE):** Established NarrativeLedger as pure
query/export facade. `record()` is for construction-time / test use, not authoritative
mutation. `CampaignState.narrative_ledger` owns the list.

**WorldEmergencePhase pattern (existing):** `QuestOpportunityRewardSystem.enforce()`
(quest_opportunity_rewards.py:106) shows how to add `WorldEvent` entries to
`world_events_add`. EventExtractor already reads them (event_extractor.py:555). This
is the correct path for `world_emergence_event`.

---

## Risks and Open Questions

### Open Questions Requiring Decisions

**Q1: world_emergence_event threshold — what triggers it?**
The ticket says "World emergence threshold crossed" but `WorldEmergencePhase.execute()`
has no threshold logic that maps to a narrative event. The closest signal is
`RegionalPressure` intensity or `WorldOpportunityPressureService` output. A concrete
threshold must be defined (e.g., any `RegionalPressure` with `intensity > 0.7`, or
any non-empty `result.opportunities`). Without a decision, implementation will be
arbitrary.

**Q2: narrative_milestone "first X" state — where does it live?**
`WorldEmergencePhase` is a `@staticmethod` with no instance state. Options:
(a) Add `AuthoritativeState.milestone_flags: frozenset[str]` (durable, survives ticks,
    requires state schema change)
(b) Add a module-level mutable set (breaks determinism — not acceptable)
(c) Detect "first occurrence" in EventExtractor by checking whether a matching event
    appeared in `state.recent_world_events` only once (fragile, depends on window size)
(d) Emit `narrative_milestone` unconditionally from EventExtractor when
    `war_declared/boss_spawned/region_ownership_changed` events fire, relying on
    NarrativeScorer's own one-shot guards (scorer already has `_quest_dormant_fired`
    pattern — add similar for milestones)

Option (d) is lowest-risk and matches the existing pattern. Decision needed.

**Q3: ScenarioRuntimeService event_recorder injection — approach?**
`ScenarioRuntimeService` is used in tests and by REST API. Adding `event_recorder` as
an optional parameter is straightforward but must be None-safe. The alternative is
detecting `ScenarioObjectiveState` changes in EventExtractor via a hypothetical state
field — but no such field exists in `AuthoritativeState`. Injecting an `event_recorder`
is the only viable path.

**Q4: hero_death_unrecorded — how to detect "no chronicle entry this tick"?**
The ticket proposes passing a "chronicled this tick" entity ID set between phases. But
phases are stateless and communicate only via `StateUpdate`. Options:
(a) Add a field to `StateUpdate` (`chronicled_entity_ids: frozenset[int]`) that
    WorldEmergencePhase populates and LifecycleSystem reads
(b) Detect in EventExtractor: check `update.entity_updates` for entities dying
    (`outcome_kind == "KILL"` or `active == False`) with `kind == "hero"` and no
    matching chronicle event in `update.world_events_add` this tick
(c) Always emit `hero_death_unrecorded` for hero-kind entity deaths (simplest; assume
    chronicle gap is the common case)

Option (b) is cleanest without StateUpdate schema changes. Option (c) produces false
negatives if NarrativeLedger was called but emits no bus event. Decision needed.

**Q5: NarrativeLedger.record() injection scope**
The ticket scopes the fix to `NarrativeLedger.__init__()` or `record()`. But
`NarrativeLedger` is a query facade — the authoritative list lives in
`CampaignState.narrative_ledger` and is populated by the campaign orchestrator. The
`record()` method docstring explicitly says it is "for construction-time or test use."
The real write path is `CampaignState.narrative_ledger.extend(entries)` in the
orchestrator. If `chronicle_entry_created` must fire when entries are written to disk
JSONL, the hook belongs in `to_jsonl()` or in the orchestrator, not in `record()`.
Confirm which call site is the authoritative write site.

### Risks

**R1: WorldEmergenceResult discarded in pipeline.py:284.**
Any `world_events_add` appended by WorldEmergencePhase IS propagated (it's part of
StateUpdate return). Adding narrative WorldEvents to `world_events_add` inside
`WorldEmergencePhase.execute()` is safe. But the `WorldEmergenceResult` itself (quest
seeds, pressures, etc.) is still discarded — this is pre-existing behavior and out of scope.

**R2: ScenarioRuntimeService tests use mock kernels.**
`_evaluate_after_tick()` at line 299 does `int(getattr(self._kernel, "_current_tick_event_count", 0))`
with an explicit defensive note about MagicMock. Injecting an `event_recorder` must
similarly be None-safe and test-friendly.

**R3: NarrativeLedger is a pure read facade; `record()` is not the authoritative path.**
If `record()` is instrumented but the orchestrator bypasses it (using
`state.narrative_ledger.extend()` directly), the event will never fire. Verify the
real write site before instrumenting.

**R4: `narrative_milestone` double-firing.**
If emitted unconditionally from EventExtractor on every `war_declared` event,
NarrativeScorer already has no one-shot guard for `narrative_milestone` (it returns
`_rec(weights["history_forming"], ...)` on every occurrence). If the intent is "fires
once per run," a guard is needed in either the emitter or the scorer.

**R5: Import constraint.**
AC requires "No import of `src/simulation_quality/` from any narrative phase." All
new emission code must stay in `src/observability/event_extractor.py` or in the
source phases (`world_emergence/phase.py`, `lifecycle.py`,
`engine/scenario_runtime.py`, `domains/campaigns/narrative_ledger.py`). No scorer
imports allowed in these files.

---

## Anti-Drift Hazards

1. **WorldEmergenceResult[0] index in pipeline.py:284** — if refactored to capture
   `[1]` for other purposes, ensure narrative events are not double-emitted.

2. **QuestEvent translation already done** — do not re-implement quest_started/
   completed/failed emission; they already fire via translation layer. Only add the
   7 missing event types.

3. **resource_transfers vs intent_results lesson** — narrative events are not economy
   events; they do not use intent_results. Use state diff, `world_events_add`, or
   direct injection.

4. **NarrativeScorer one-shot flags** — `_quest_dormant_fired`, `_narrative_silent_fired`,
   `_scenario_broken_fired` are instance-level guards. Any repeated `scenario_stalled`
   emission is correctly deduplicated by the scorer. Do not add scorer-level guards in
   the emitter.

5. **hero kind check** — entity `kind` field is set in builder (builder.py:91); not
   all entities have `kind == "hero"`. Boss entities use `kind in {"world_boss",
   "ancient_sentinel"}` (event_extractor.py:481). The `hero_death_unrecorded` detection
   must check `entity.kind == "hero"` (or the configured hero kind set).
