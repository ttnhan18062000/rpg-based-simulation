---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-GRIEF-NEMESIS-REACHABILITY
artifact_type: investigation
tags: [cognition, social, observability]
---

# Investigation — TCK-20260824-GRIEF-NEMESIS-REACHABILITY

## Context-search note

`mcp__knowledge-search__search_docs` was attempted for this ticket's topic by the orchestrator
before this investigation started and returned `{"error":"index not found"}` — a pre-existing
environment gap (index not built), not something this investigation routed around. `graphify
query "campaign orchestrator run_episode register_campaign SimQ event_type entity_death
authoritative pipeline"` was run by the orchestrator and confirmed `register_campaign()` has zero
production callers. This investigation ran further targeted `grep`/`Read` passes (documented
fallback per CLAUDE.md when semantic search is unavailable) rather than re-running graphify for
narrower sub-questions, since graphify's own community/edge index would not resolve the specific
call-chain and dead-code questions below any better than direct source tracing.

## Current Behavior

### CampaignOrchestrator — episode-boundary-only grief/nemesis trigger

`src/domains/campaigns/orchestrator.py`:
- `run_episode()` (lines 151-185) runs one episode via `ScenarioRuntimeService`, then calls
  `_advance_state()` (line 184).
- `_advance_state()` (189-222) calls `_advance_grief_urgencies()` (209) and
  `_advance_nemesis_relations()` (211) — **once, at episode end**, using
  `NarrativeLedgerEntry` records converted from `final_state.recent_world_events` at
  `_extract_narrative_entries()` (408-446).
- `_advance_grief_urgencies()` (224-268): decays existing `GriefUrgencyModifier`s, then scans
  `new_entries` for `event_type == "entity_death"` and creates a modifier for any social-memory
  ally with `trust_score >= ALLY_TRUST_THRESHOLD` (0.30).
- `_advance_nemesis_relations()` (270-306): scans `SocialMemoryRecord.interaction_history` for
  antagonism-kind interactions across 2+ distinct episodes, forming/updating `NemesisRelation`.
- `_build_initial_state()` (483-618) is the **only** call site that applies the importers: lines
  567-571 (`GriefUrgencyImporter.apply`) and 576-579 (`NemesisRelationImporter.apply`), at the
  *start* of the next episode. There is no mid-episode call anywhere.
- `run_episode()` constructs `ScenarioRuntimeService(spec, initial_state=initial_state)` at line
  172 **without** passing `self._event_recorder` through — the per-episode kernel run has no
  event recorder unless a future change wires one in. Only `_emit_chronicle_events()` (308-336),
  called from `_advance_state()` at episode end, uses `self._event_recorder`.

### GriefUrgencyImporter / NemesisRelationImporter — direct-EntityState-return shape

`src/domains/campaigns/grief_urgency.py`:
- `GriefUrgencyImporter.apply()` (43-63): builds a `ConcernState(kind=SOCIAL_THREAT, id="grief_ally_{dead_ally_id}", urgency=modifier.urgency)`, merges it into a **copy** of
  `entity.strategic.concerns` via `dc_replace`, and returns a **whole new `EntityState`**
  (`dc_replace(entity, strategic=new_strategic)`). It does not return or emit any typed `Update`
  object.
- `NemesisRelationImporter.apply()` (79-93): same shape — builds a `BlockerState(kind=SOCIAL,
  id="nemesis_{antagonist_id}")`, merges into a copy of `entity.strategic.blockers`, returns a new
  `EntityState`.
- Both are only safe to call because `_build_initial_state()` is building a **brand-new**
  `AuthoritativeState` from scratch (episode 0 has no state at all yet) — there is no concurrent
  authoritative mutation in flight to race against. That safety property does **not** carry over
  to a mid-episode call, where the entity is live inside a running `Kernel` tick and any direct
  return of a whole `EntityState` bypasses `ApplyPath`/`DirtySet` tracking entirely
  (Hard Rule: "Do not mutate durable state outside authoritative flows").

### The tick-time typed-update pattern these importers must reconcile against

`src/core/updates.py`:
- `StrategicUpdate` (474-576) has `concerns_add_or_update: list[ConcernState]` (493) and
  `blockers_add_or_update: list[BlockerState]` (477) fields — **exactly** the two collections
  `GriefUrgencyImporter`/`NemesisRelationImporter` mutate today, already modeled as a typed,
  additive, mergeable update.
- `EntityUpdate.strategic: Optional[StrategicUpdate]` (636) is how decision logic attaches a
  `StrategicUpdate` for the authoritative apply path to consume.

`src/engine/patches.py` (`StrategicPatch.apply()`, 415-455): merges `concerns_add_or_update` /
`blockers_add_or_update` into `entity.strategic.concerns`/`.blockers` via `merge_dict()` (421-429,
441/445) — the actual authoritative-pipeline consumer of the two fields.

`src/engine/tactical.py:186-196` is a **concrete existing reference** for the pattern the ticket
needs: live tactical decision logic builds `StrategicUpdate(projects_add_or_update=[...],
current_project_id_set="", ...)` and returns it wrapped in an `EntityUpdate`, which flows through
`ApplyPath`/`StrategicPatch` normally — the same authoritative path any new mid-episode grief/nemesis
trigger must use instead of `GriefUrgencyImporter.apply()`'s direct-return shape.

**Reconciliation finding**: `GriefUrgencyImporter.apply()`/`NemesisRelationImporter.apply()` can be
adapted to build and return a `StrategicUpdate(concerns_add_or_update=[concern])` /
`StrategicUpdate(blockers_add_or_update=[blocker])` instead of a whole `EntityState`, while
preserving the existing episode-boundary call site's guarantee (`_build_initial_state()` is
building fresh state directly, not applying through a `Kernel` tick, so it can either keep calling
a state-returning wrapper or apply a returned `StrategicUpdate` via `StrategicPatch`/`ApplyPath`
directly against the freshly-constructed entity). The safest reconciliation is two thin entry
points on the same underlying builder: one that returns the `StrategicUpdate` (for the new
mid-episode caller, which must go through `ApplyPath`), and one that keeps returning a whole
`EntityState` for `_build_initial_state()`'s existing pre-`Kernel` construction use, sharing the
concern/blocker-building logic so the two paths cannot drift.

### Where in-episode entity death is actually detected today (mid-tick)

`src/observability/event_extractor.py:483` — `if prior_ent.lifecycle.active and not
entity.lifecycle.active:` is the **existing production detection point** for a lifecycle
active→False transition mid-tick. It already branches to emit `CombatKillEvent` (495-498, gated on
`death_reason == "COMBAT"` and not shaper-owned) and a NARRATIVE `hero_death_unrecorded`
`SimulationEvent` (505-514, unconditional on `entity.kind == "hero"`). This is the natural hook
point for a new mid-episode grief/nemesis trigger — either directly (call a new
`GriefUrgencyTrigger`-style service from here and merge its `StrategicUpdate` into the tick's
`update`) or by emitting a `grief_urgency_triggered`/`nemesis_relation_formed`-adjacent detection
signal that a downstream phase consumes.

**Gap found**: nothing in production code ever constructs `WorldEvent(category=WorldEventCategory.ENTITY_DEATH, ...)`. `ENTITY_DEATH` is defined in
`src/domains/world_emergence/schema.py:16` and **consumed** by `src/domains/world_emergence/services.py:180`,
`models.py:38`, and `phase.py:69`, but grepping all of `src/` for `WorldEvent(category=` producers
(`src/engine/economy.py`, `src/engine/military_conflict.py`, `src/engine/world_dynamics.py`) shows
only `RESOURCE_DEPLETED` and faction/diplomacy categories are ever actually appended —
`ENTITY_DEATH` only appears in test fixtures. This means `CampaignOrchestrator._extract_narrative_entries()`'s
`"ENTITY_DEATH"` branch of `_SIGNIFICANCE_MAP` (orchestrator.py:58) is currently **dead in
practice for any live-tick death** — the entity_death `NarrativeLedgerEntry`s it has ever produced
in a real run would have to come from some other path that also never fires, since `recent_world_events`
never actually contains an `ENTITY_DEATH`-category `WorldEvent`. (Existing unit tests construct
`WorldEvent(category="ENTITY_DEATH", ...)` fixtures by hand — see
`tests/unit/domains/campaigns/test_narrative_ledger.py` — so the *conversion* logic is tested, but
the producer side is not.) The `event_extractor.py:483` lifecycle-transition detection is the real,
already-firing mid-tick death signal — not the `WorldEvent`/`recent_world_events` path the
episode-boundary code currently reads. Any new mid-episode grief/nemesis trigger should be built on
the `event_extractor.py:483` transition, not on wiring an `ENTITY_DEATH` `WorldEvent` producer that
does not otherwise exist (that would be new, out-of-scope infrastructure for a different problem).

### SimulationEvent / event_type pattern to follow for new event types

`src/observability/events.py`: `SimulationEvent` (54-77) is the base Pydantic model; concrete event
types are subclasses with a fixed `event_type`/`event_category`/`source_system` and an
auto-generated `message` (e.g. `LeadershipChangedEvent` 276-299, `event_category="social"`,
`source_system="party_lifecycle_service"`). `LegendaryArrivalEvent`/`KnownTraitorSpottedEvent`/
`OldDebtCollectedEvent` (357-431) are the closest existing analogue — all `event_category="social"`,
sourced from cross-episode social-memory consequences (`social_consequence_evaluator`), which is
architecturally the same shape as "cross-episode social state (grief/nemesis) becomes an in-episode
signal." A `GriefUrgencyTriggeredEvent`/`NemesisRelationFormedEvent` pair following this exact
pattern (`event_category="social"`, `source_system="campaign_orchestrator"` or a new
`grief_nemesis_service`) is the natural fit — not a bare `SimulationEvent(event_type=..., ...)`
call, though that is also a valid, lighter-weight option matching `demographic_mortality`'s pattern
at `event_extractor.py:195-200`.

### SimQ pillar wiring — which pillar can query these event_types

`src/simulation_quality/scorers/narrative.py` (`NarrativeScorer`, `PILLAR_ID = PillarId.NARRATIVE`):
`EVENT_TYPES` (22-33) is a fixed tuple the scorer's `score()` matches against with `if et ==`
branches — adding a new event_type here requires both the tuple entry and a new branch, plus a
corresponding weight key in `config/simulation_quality/scoring_weights.yaml`'s `NARRATIVE:`
section (consumed via `self.weights["<key>"]`, `ScoringWeights.__getitem__`,
`src/simulation_quality/weights.py:111`). `hero_death_unrecorded` (125-130) is the closest existing
analogue — same "a lifecycle-transition mid-episode signal becomes a NARRATIVE score" shape.

`src/simulation_quality/scorers/social.py` (`SocialScorer`, `PILLAR_ID = PillarId.SOCIAL`) is the
other real candidate: `EVENT_TYPES` (19-31) already covers `social_memory_created`,
`reputation_delta`, `group_joined`/`group_expelled` — grief/nemesis are social-memory-derived
concern/blocker injections, arguably a closer semantic fit than NARRATIVE (whose scorer docstring
explicitly says it "Does NOT duplicate FactionScorer signals" — a boundary-drawing precedent for
keeping narrative-specific vs. social-specific signals apart). **This is the ticket's own listed
open decision** ("Decide the event_category (social/strategy) and whether it counts toward the
NARRATIVE pillar or needs a new one") — not resolved here per the ticket's scope, but the concrete
finding is: both pillars are mechanically wireable with the same shape of change (tuple entry +
`if et ==` branch + weight key), so the choice is a design/semantics call, not a feasibility
question. Recommendation: `event_category="social"` (matches every existing cross-episode-consequence
event and both `ConcernState`/`BlockerState` targets, which already live under
`entity.strategic.*` fed by social-memory data) and pillar `SOCIAL` (matches `SocialScorer`'s
existing `social_memory_created`/`reputation_delta` semantic family more closely than
`NarrativeScorer`'s quest/chronicle-milestone family) — but this is a recommendation, not a
pre-made decision; the ticket explicitly leaves it open.

### SimQ scenario/corpus profile system — architecturally does not reach CampaignOrchestrator

`config/simulation_quality/profiles/*.yaml` (18 files) are **not** scenario/campaign definitions —
each is a `pillar_weights:` override map plus an optional `feature_flags:` block (e.g.
`urban_political.yaml`: `pillar_weights: {FACTION: 1.5, ...}`, `feature_flags: {ENABLE_SOCIAL_COOPERATION: "ON", ...}`).
`config/simulation_quality/corpus_registry.yaml` (machine-generated by
`tools/generate_corpus_registry.py` from `tests/simulation_quality/fixtures/grade_anchors.json` —
**not** hand-authored) maps `run_key` → `{profile_name, seed, ticks, world_name, active_feature_flags}`.

The actual execution entry point is `tools/calibrate_simq.py::_run_engine()` (164-...): it loads a
compiled `WorldSpec` (or falls back to a generic hero+goblins scenario), constructs one
`AuthoritativeState`, and drives `Kernel` directly for N ticks in a **single continuous run** — it
never touches `ScenarioRuntimeService` or `CampaignOrchestrator` at all. `main()` (368-...) then
replays the run's `simulation_events.jsonl` through `QualityHub` (`_replay_jsonl_through_hub()`,
340-364).

**Grep confirmation**: `grep -rln "CampaignOrchestrator|CampaignManifest" --include="*.py" .` outside
`tests/` matches only `src/api/routes/campaigns.py` (a docstring comment, not an import — the file
only imports `CampaignState`) and the campaign-domain modules themselves
(`orchestrator.py`, `grief_urgency.py`, `social_memory.py`, `state.py`, `plan_revision.py`,
`progression_plan.py`, `src/domains/culture/exporter.py`). No tool, no SimQ scorer, no route, no
CLI script ever constructs a `CampaignOrchestrator` or `CampaignManifest` in production. This
independently confirms the orchestrator's earlier `graphify` finding
("`register_campaign()` has zero production callers").

**Implication for "make reachable" (already-decided direction)**: extending an *existing* SimQ
profile YAML alone (adding `pillar_weights`/`feature_flags` keys) cannot make
`CampaignOrchestrator.run_episode()` execute, because none of the current profiles are consumed by
anything that knows how to run multiple episodes — `calibrate_simq.py::_run_engine()` runs exactly
one `Kernel` loop over one `AuthoritativeState`. Making a real profile reach `run_episode()`
requires either (a) a new campaign-aware branch in `calibrate_simq.py` (or a small parallel runner)
that, for a designated profile/run_key, builds a `CampaignManifest` (N `SimulationScenarioDefinition`
episodes) and calls `CampaignOrchestrator.run_episode()` N times instead of calling `Kernel.tick_once()`
directly, feeding the accumulated per-episode `EventRecorder` output into the same
`simulation_events.jsonl` → `QualityHub` replay `calibrate_simq.py` already does; or (b) wiring
`self._event_recorder` through to the per-episode `ScenarioRuntimeService(spec, initial_state=...,
event_recorder=self._event_recorder)` call at `orchestrator.py:172` (currently omitted — see
Current Behavior above) so that an episode's in-`Kernel` events (including the new mid-episode
`event_extractor.py:483`-triggered grief/nemesis events) actually reach an `EventRecorder` at all,
which is a prerequisite for either integration shape. `ScenarioRuntimeService` (`src/engine/scenario_runtime.py`,
accepts `event_recorder` at `__init__`, line ~135) is a more natural integration point than
`calibrate_simq.py`'s raw `Kernel.tick_once()` loop, since it already has the event-recorder plumbing
`CampaignOrchestrator` expects — but no existing profile or corpus entry currently names a
multi-episode manifest, so a new profile (or a repurposed existing one, e.g. `lifecycle_full_coverage_world`
which already stresses lifecycle transitions) plus a small runner-side branch is required either
way. This is a real, non-trivial integration gap, not a config-only change — flagged as an open
question below since the exact shape (new profile vs. extend an existing one; new `calibrate_simq.py`
branch vs. new small script) is an implementation-planning decision, not something this
investigation should pre-commit to.

## Mechanics / Engine Constraints

- **Strategic layer model** (`docs/mechanics/04_strategic_cognition.md` §3 "Strategic Memory:
  Leads & Blockers", line 86 onward): `ConcernState`/`BlockerState` are the authoritative
  in-memory representation of strategic-layer urgency/obstruction signals — grief and nemesis both
  already conform to this (concerns for grief, blockers for nemesis). §2a documents the existing
  `compute_danger_urgency()` → `ConcernState`-generation pattern (regional danger urgency,
  `src/systems/world_systems/events.py`) as the closest precedent for "a detected condition
  produces a `ConcernState` every tick it holds" — grief/nemesis's mid-episode trigger should follow
  this same tick-repeatable-detection shape rather than a one-shot injection, though the ticket
  scope note ("the same grief-urgency concern injection within the same episode") suggests a
  single injection per death event is what's wanted, not per-tick regeneration.
- **Authoritative Mutation Pipeline** (Hard Rule / `docs/engine/authoritative_mutation_pipeline_contract.md`):
  decision logic must not directly mutate durable state; `StrategicPatch`/`ApplyPath` is the only
  legitimate application point for `entity.strategic.concerns`/`.blockers` changes during a live
  tick. This is the core constraint the direct-`EntityState`-return shape in `grief_urgency.py`
  currently violates for any mid-episode use (it is currently only safe because its one call site
  runs before any `Kernel` tick exists).
- **7-phase kernel loop** (`docs/engine/kernel.md`): a new mid-episode trigger fired from
  `event_extractor.py` (an Observability-phase consumer, post-Resolution) means the resulting
  `StrategicUpdate` cannot be applied within the *same* tick's `ApplyPath` pass that produced the
  death (event extraction reads the already-applied `current_state`/`prior_state` diff) — it would
  need to be applied on a subsequent tick, or `event_extractor.py`'s call site would need to move
  earlier in the phase order, or the death-detection condition (`lifecycle.active` transition)
  would need to be re-checked directly inside a Resolution-phase system instead of Observability.
  This is a design decision for planning, not resolved here.

## Docs Requiring Update

- `docs/parity_ledger/social_narrative.yaml`: SOC-231 (grief urgency, currently `status: verified`,
  text scoped to "episode-start" injection only) and SOC-232 (nemesis relation, same) both need
  their `text`/`status`/`v2_evidence` updated once a mid-episode trigger path exists — their
  current text is accurate for the existing behavior but will become incomplete/stale the moment
  in-episode triggering ships, per the Authoritative Mechanics Rule ("If logic changes, update the
  corresponding doc AND the parity ledger entry in the same session").
- `docs/mechanics/04_strategic_cognition.md`: needs a new subsection (or an addition to §3
  "Strategic Memory: Leads & Blockers") documenting the new mid-episode grief/nemesis trigger path
  and the `StrategicUpdate`-based mutation shape, since this ticket adds a second, tick-time
  injection mechanism alongside the existing episode-boundary one and the Mechanics Bible is the
  authoritative source for strategic-layer behavior.

The `docs/engine/contracts/rpg_refinement_pillars.md` doc (path:
`docs/engine/contracts/rpg_refinement_pillars.md`, under `docs/engine/contracts/`) is not required
to change for this ticket: its one relevant line (57, "the Nemesis System... marks high-impact
attackers as priority targets that override standard AI scoring") describes the broader
scoring-override Nemesis System, which the ticket's own Out of Scope section explicitly excludes
as "a pre-existing possible divergence, noted but not resolved here."

## Parity Ledger Overlap

- `docs/parity_ledger/social_narrative.yaml`:
  - **SOC-231** — grief/rage urgency (E43F). `status: verified`, `priority: P1`. Text and
    `v2_evidence` describe only the episode-boundary path (`_advance_grief_urgencies`,
    `GriefUrgencyImporter.apply()` called from `_build_initial_state()`). Will need updating once
    the mid-episode trigger exists (not P0, so no `test_path` gate blocks this ticket, but the
    Authoritative Mechanics Rule still requires the update in the same session as the code change).
  - **SOC-232** — nemesis relation (E43G). `status: verified`, `priority: P1`. Same situation as
    SOC-231.
  - **SOC-066** and `docs/parity_ledger/strategic_cognition.yaml`'s **STRAT-143**/**STRAT-144** all
    reference a *different*, legacy "nemesis" concept (`entity.social.nemesis_ids` /
    `check_nemesis_promotion()` in `src/systems/social_systems/memory.py`, grudge-threshold based) —
    unrelated to `CampaignState.nemesis_relations` (`NemesisRelation`, cross-episode antagonism
    count based). Confirmed by code: `check_nemesis_promotion()` only touches
    `entity.social.grudge_history`/`.nemesis_ids` via `SocialUpdate.nemesis_promotion`
    (`src/core/updates.py:295`, applied in `src/systems/social_systems/relationships.py:67`) — a
    completely separate field and mechanism from `CampaignState.nemesis_relations`. No overlap; no
    action needed on these three entries. This matches the ticket's own Out of Scope note that
    `check_nemesis_promotion()`/`tick_place_attachment()` are "completely unrelated," tracked
    separately as `TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`.

No P0 parity entries are touched by this ticket's scope.

## Prior Work

- `tickets/done/TCK-20260628-E43F-GRIEF-URGENCY.md`: original grief-urgency implementation.
  Confirms the episode-boundary-only design was intentional at the time ("Out of Scope:... Route
  scoring adjustment based on grief urgency (follow-on work)") — this ticket is exactly that kind
  of follow-on, now specifically for mid-episode reachability.
- `tickets/done/TCK-20260628-E43G-NEMESIS-RELATION.md` and
  `tickets/done/TCK-20260628-E43H-NARRATIVE-OBS.md`: not read in full detail beyond confirming
  their existence and topic (nemesis relation formation; decision-trace observability surface for
  E43F/E43G) — no additional reachability-relevant findings beyond what E43F's ticket and the live
  source already show.
- `stored_artifacts/TCK-20260619-E32B-CAMPAIGN-STATE/` and
  `stored_artifacts/TCK-20260619-E32-CAMPAIGN-RUNTIME/`: original `CampaignState`/
  `CampaignOrchestrator` scaffolding tickets. No `REGISTRY.yaml` exists yet in this repo snapshot
  (confirmed: no `docs/REGISTRY.yaml` found), so prior-work discovery here used the documented
  fallback path — `tickets/done/` filtered by name similarity (`E43F`/`E43G`/`E43H`, `CAMPAIGN`)
  plus a `stored_artifacts/` directory-name join, not a registry query.
- No prior investigation specifically targets "reachability" of `CampaignOrchestrator` from SimQ or
  production — this is new ground, consistent with the ticket's own framing (a depth-audit finding,
  not a continuation of prior scoped work).

## Risks and Open Questions

- **Open, ticket-flagged**: exact mechanism for "reachable" (new CLI script vs. scenario content
  vs. documented API trigger) is explicitly left to the implementation-planning phase by the ticket
  author, but the *decision-already-made* framing from the parent orchestrator constrains this to
  "wire into an existing SimQ scenario/corpus profile." Given the investigation finding above (no
  existing profile reaches `run_episode()` — the whole SimQ harness is single-episode), the
  concrete implementation choice (new profile + new `calibrate_simq.py` branch vs. a small parallel
  campaign-aware runner script) is a real design decision for `plan.md`, not something this
  investigation resolves.
- **Open, ticket-flagged**: `event_category` (social vs. strategy) and pillar (NARRATIVE vs. SOCIAL
  vs. new) for the new event_type(s) — both are mechanically feasible (see SimQ pillar wiring
  section above); this investigation recommends `social`/`SOCIAL` but does not treat that as
  decided.
- **Newly found, not previously flagged**: `WorldEventCategory.ENTITY_DEATH` is never produced in
  production — only consumed. If a future change assumed the episode-boundary
  `_extract_narrative_entries()` path was already receiving real entity-death signals from live
  runs, that assumption is wrong; it currently only works in tests that hand-construct the
  `WorldEvent` fixture. This ticket's mid-episode trigger should be built on the
  `event_extractor.py:483` lifecycle-transition signal (which does fire in production), not on
  wiring a new `ENTITY_DEATH` `WorldEvent` producer (out of scope — a larger, separate gap).
- **Newly found**: `CampaignOrchestrator.run_episode()` does not pass `self._event_recorder` through
  to the per-episode `ScenarioRuntimeService` (`orchestrator.py:172`). Any mid-episode
  event emission (`grief_urgency_triggered`/`nemesis_relation_formed`) requires this to be wired
  first, or the events will have nowhere to go during the episode itself.
- **Risk**: the 7-phase kernel loop ordering constraint (see Mechanics/Engine Constraints above) —
  `event_extractor.py` runs after `ApplyPath` for the tick that produced the death, so a
  same-tick, same-`ApplyPath`-pass application of the resulting `StrategicUpdate` is not possible
  without restructuring where the trigger fires. The ticket's acceptance criterion says "within the
  same episode" (not "within the same tick"), which this constraint is compatible with, but
  `plan.md` should make the tick-vs-episode timing explicit to avoid an implementer assuming
  same-tick application is required (or possible) when it isn't with the current phase ordering.

## Anti-Drift Hazards

- Do not conflate `CampaignState.nemesis_relations`/`NemesisRelation` (this ticket's subject) with
  `entity.social.nemesis_ids`/`check_nemesis_promotion()` (the unrelated legacy grudge-threshold
  mechanism, tracked by `TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`). They share the word "nemesis"
  and nothing else — different data model, different trigger condition, different file.
  `src/systems/social_systems/memory.py` must not be touched by this ticket's implementation.
  `src/domains/adventure/generator.py`'s FORM_PARTY blocker check (which reads
  `entity.strategic.blockers` for `NemesisRelationImporter`-injected `BlockerState`s) is the correct
  file if party-formation-blocking behavior needs verification — not `memory.py`.
  `check_nemesis_promotion()`/`tick_place_attachment()` unit test coverage is explicitly out of
  scope here.
- Do not resolve or touch the "Nemesis System overriding AI scoring" divergence noted in
  `docs/engine/contracts/rpg_refinement_pillars.md:57` — explicitly out of scope per the ticket.
- Do not build an `ENTITY_DEATH` `WorldEvent` producer as a side effect of making the mid-episode
  trigger work — the existing `event_extractor.py:483` lifecycle-transition signal is sufficient
  and already fires in production; adding a new `WorldEvent` producer is unscoped, larger
  infrastructure work with its own blast radius. It would also start flowing into
  `WorldEmergencePhase`'s `QuestOpportunityGenerator.from_threat_signal()` path
  (`phase.py:69`) — a currently-dormant consumer this ticket should not accidentally activate as a
  side effect.
- Do not widen scope to wiring `self._event_recorder` through every use of
  `ScenarioRuntimeService` project-wide; only `CampaignOrchestrator.run_episode()`'s specific call
  site (`orchestrator.py:172`) is implicated by this ticket.
- Do not let the "reconcile the direct-return mutation shape" work regress
  `_build_initial_state()`'s existing behavior/tests (`tests/unit/domains/campaigns/test_grief_urgency.py`,
  `test_campaign_orchestrator.py`) — the episode-boundary call site's contract (immutable input,
  new `EntityState` out, used while constructing a brand-new `AuthoritativeState`) must keep
  working unchanged even after a `StrategicUpdate`-based path is added for the mid-episode caller.
- Do not implement the new SimQ profile/runner change by hand-editing
  `config/simulation_quality/corpus_registry.yaml` — it is machine-generated by
  `tools/generate_corpus_registry.py` from `grade_anchors.json`; any new campaign-aware profile
  must go through that generation path (`make simq-corpus-registry`) to stay in sync, per that
  file's own header comment.
