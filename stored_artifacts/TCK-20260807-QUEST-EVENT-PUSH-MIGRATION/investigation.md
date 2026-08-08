---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# Investigation: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION

## Corrected understanding of where quest_event actually comes from

`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`'s own "Out of Scope" section states:
"`quest_event` (quest_started/completed/failed) — confirmed via raw JSONL inspection this session
to already come from `quest_system`, a separate live-emission source, **not**
`event_extractor.py`'s diffing pass."

Direct code reading contradicts this: `event_extractor.py:787-823` (prior to this ticket)
constructs `QuestEvent` unconditionally inside the ordinary per-entity post-tick diffing loop —
the exact code `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` fixed a bug in, the very next day after
the epic closed. Confirmed no `_push_shapers_active`/`_push_shapers_phase2_active` gate wraps
this block (unlike every genuinely-migrated domain in the same file).

The real, separate live-emission mechanism the epic's inspection likely saw is
`QuestOpportunityRewardSystem.resolve()`'s `WorldEvent(category=WorldEventCategory.QUEST_COMPLETED)`
(`src/engine/pipeline_phases/quest_opportunity_rewards.py:107`) — a different system entirely: it
operates on `state.quest_registry`'s `QuestOpportunity` entries (world-level, E23C), not
`entity.strategic.projects`' `QuestState` entries (entity-project, what `quest_event`/`SOC-241`
actually tracks). Likely explanation for the epic's own JSONL inspection: `quest_event`'s raw hit
count was near-zero at the time (real quest generation wasn't wired into live gameplay until
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`, landed the same session as this investigation, and
`quest_event` itself had its own type-filter bug making its output meaningless even when it did
fire) — a superficial trace of near-zero output was likely misread as "doesn't come from here,"
rather than confirmed by reading the construction code directly.

## Systematic sweep for other push-shaper gaps

Per the user's request ("create tickets if you find that an event should be pushed and calculated
as a scoring metric"), swept every `event_extractor.py` block for push-shaper gating (grepped all
`_push_shapers_active`/`_push_shapers_phase2_active` check sites, then read every un-matched
`events.append(`/`QuestEvent(` construction site to classify it):

| Block | Gated? | Scored? | Disposition |
|---|---|---|---|
| `quest_event` | No (fixed this ticket) | Yes (`NarrativeScorer`) | **Fixed — this ticket** |
| `commitment_abandoned` | No | Yes (`AgencyScorer`) | Real gap — filed `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP` |
| `rejection_cascade_tick` | No | Yes (`AgencyScorer`) | Real gap — filed `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP` |
| `capability_growth_stalled`/`life_arc_incoherent` | No | Yes (`ProgressionScorer`) | NOT a gap — genuinely new signal added after Phase 2 closed, no shaper equivalent ever existed, explicitly documented in its own code comment as deliberately unguarded (no double-fire risk). Not filed. |
| Everything else in the file | Yes | — | Already migrated (Phase 1 or Phase 2), rollback path intact |

Confirmed the file's structure is otherwise fully accounted for: read from line 1 to line 1408
(end of file), every `events.append`/event-construction site outside the two intentional-new-
signal blocks falls inside a `_push_shapers_active`/`_push_shapers_phase2_active` guard.

`docs/simulation_quality/event_type_coverage.md`'s own "source" column is stale for most rows
(still lists dozens of already-migrated events as `event_extractor` sourced) — not used as
evidence for this sweep; only live code reading was trusted.

## Reconstruction path design

`NarrativeShaper` needs to detect `QuestState.quest_status` transitions without reading post-apply
`current_state` (per this module's own architecture — see `event_shapers.py`'s own docstring).
Added `_current_projects(prior_ent, strategic_upd)`, mirroring the already-proven
`_current_leads()` helper exactly: `prior_ent.strategic.projects` (full snapshot) +
`strategic_upd.projects_add_or_update`/`projects_remove` (this tick's delta) == current full
`projects` dict, since `AuthoritativeState` is a full snapshot each tick, not an incremental
structure. Confirmed sufficient (not approximate) for the same reason `_current_leads()` is:
`entity_updates.items()` already scopes to only entities with SOME update this tick, matching
`event_extractor.py`'s own `dirty_entity_ids` precondition.

## Flag design: own flag, not reusing Phase 2's

`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` already defaults `ON`. Registering `NarrativeShaper` directly
into `PHASE2_SHAPER_REGISTRY` would have delivered it live immediately with zero SHADOW-validation
window — the identical mistake `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY` already found and
fixed once when Phase 2 itself needed its own flag distinct from Phase 1's (self_model_updated/
cooperation_event double-firing, documented in that ticket's own investigation.md). New,
dedicated `ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag added instead, with its own gating logic inside
`run_shadow_shapers()`, mirroring the Phase 2 block's exact structure (construct in SHADOW,
deliver only in ON).

## Real-kernel-adjacent verification

Built a real `AuthoritativeState`/`StateUpdate`/`StrategicUpdate` pair (via `V2EntityBuilder`, not
mocks) representing a hero with one quest transitioning `ACTIVE` → `COMPLETED`, and called both
`EventExtractor.extract()` and `run_shadow_shapers()` directly:

- **Default (flag absent → "ON")**: extractor's own quest_event count = 0 (correctly suppressed);
  shaper's quest_event count = 1, `status="completed"`, `payload={"status": "completed"}`
  (correctly delivered, correct payload).
- **Explicit `ENABLE_PUSH_EVENT_SHAPERS_QUEST="OFF"`**: extractor's own count = 1 (rollback path
  correctly restored); shaper's count = 0 (correctly suppressed).

No double-fire in either mode. Confirmed the flag correctly reaches `run_shadow_shapers()` via
`prior_state.feature_flags`, and that `Kernel._phase_observability()`'s own outer gate
(`ENABLE_PUSH_EVENT_SHAPERS`, Phase 1's flag, which wraps the ENTIRE call to
`run_shadow_shapers()`) doesn't interfere — since Phase 1 defaults `ON`, `run_shadow_shapers()`
gets called and its own internal Quest-mode gating (mirroring Phase 2's own nested gating)
correctly determines what's actually delivered.
