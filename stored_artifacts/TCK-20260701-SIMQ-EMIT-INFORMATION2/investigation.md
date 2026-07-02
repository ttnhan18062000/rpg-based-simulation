---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-INFORMATION2
artifact_type: investigation
tags: [simq, information, cognition, event-emission]
---

# Investigation: TCK-20260701-SIMQ-EMIT-INFORMATION2

## Current Behavior (file:line refs)

### Existing INFORMATION / COGNITION emitters (from TCK-20260629-SIMQ-EMIT-COGNITION)

| Event | Location | Signal |
|---|---|---|
| `self_model_updated` | `event_extractor.py:241` | `e_upd.self_model_bundle_set is not None` |
| `belief_assimilated` | `event_extractor.py:252` | `prop["last_assimilated_tick"] == tick` |
| `belief_updated` | `event_extractor.py:258` | co-emitted with `belief_assimilated` |
| `paid_information_transaction` | `event_extractor.py:322` | `intent_result.source_kind == "INFORMATION_PURCHASE"` |
| `lead_certainty_changed` | `event_extractor.py:349` | state-diff: `lead.certainty != prior_lead.certainty` |

### `lead_contradiction.py` — what fires and what does not

`LeadContradictionSystem.enforce()` (`src/engine/pipeline_phases/lead_contradiction.py:112`) runs a
sorted scan of all alive entities' non-EXHAUSTED leads. When `_is_lead_contradicted()` returns True,
the system:

1. Marks lead `EXHAUSTED`, `test_outcome="FAILURE"`, increments `failure_count` (line 153)
2. Enqueues `StrategicUpdate(leads_add_or_update=[failed_lead])` (line 162)
3. Enqueues `UnknownFact(subject=lead.subject, reason="lead_contradicted")` for replanning (line 166)
4. Decrements provider `reliability_score` by 0.1 (lines 198-210)
5. Emits `SimulationEvent(event_type="belief_contradiction", ...)` (line 215)

The `belief_contradiction` event is emitted at line 215 with payload `{lead_id, provider_id, subject,
old_certainty, failure_count}`.

**Gap**: There is no second event at the end of `enforce()` for `lead_contradiction_resolved`. The
"resolution" (replanning triggered, provider penalised) is represented only in the typed updates, not
as a separate observable event. The `belief_contradiction` and the resolution are logically inseparable
in this function — adding `lead_contradiction_resolved` is a second `SimulationEvent` in the same
iteration block, appended immediately after `events.append(event)` at line 234.

### `lead_certainty_changed` vs `lead_certainty_updated` — the band-crossing distinction

`lead_certainty_changed` fires at `event_extractor.py:349` on ANY difference between
`lead.certainty` and `prior_lead.certainty` (enum value diff). Its payload carries only string fields:
`from_certainty` (str), `to_certainty` (str). No numeric `certainty_delta` is set.

**Pre-existing scorer/emitter payload mismatch**: `CognitionScorer.score()` for `lead_certainty_changed`
(cognition.py:69) calls `payload.get("certainty_delta", 0.0)`, which always returns `0.0` because the
emitter does not set this key. Consequently, the `knowledge_sharpening` and `knowledge_rot` tags in
`CognitionScorer` are dead code — they never fire.

`LeadCertainty` is a string enum (`src/core/strategic.py:34`) with four values only:
`VAGUE`, `APPROXIMATE`, `PRECISE`, `EXHAUSTED`. There are no numeric certainty floats. The ticket's
"0.25 / 0.5 / 0.75 band thresholds" do not correspond to any existing field — the ordinal rank of
the enum values is the only available proxy.

Proposed ordinal mapping for band-crossing detection:
- VAGUE = 0, APPROXIMATE = 1, PRECISE = 2, EXHAUSTED = 3

`lead_certainty_updated` (InformationScorer) should emit when `rank(to_certainty) != rank(from_certainty)`
(i.e., the band changes). Its payload must include a numeric `certainty_delta` (ordinal diff / 3.0
normalised, or raw ordinal diff as int) so that `InformationScorer.score()` and `CognitionScorer.score()`
can read `payload.get("certainty_delta")` correctly. The existing `lead_certainty_changed` payload
should be extended to include `certainty_delta` as a fix.

### `LeadState` staleness — `last_updated_tick` does not exist

`LeadState` (`src/core/strategic.py:207`) fields: `id`, `kind`, `subject`, `detail`,
`discovered_tick`, `certainty`, `source_entity_id`, `tested`, `test_outcome`, `failure_count`,
`suppression_until_tick`.

**Critical gap**: `last_updated_tick` is referenced in the ticket acceptance criteria but does not
exist in `LeadState`. Staleness must be based on `discovered_tick` (age = `tick - lead.discovered_tick`).
The detection condition becomes: `(tick - lead.discovered_tick) > belief_stale_ticks threshold AND
lead.certainty not EXHAUSTED AND lead.certainty not PRECISE`.

`detection_params.yaml` (`config/simulation_quality/detection_params.yaml`) currently has
`belief_dormant_window: 100` but no `belief_stale_ticks` key. This must be added.

Deduplication: `belief_stale` must emit at most once per lead per staleness epoch (not every tick).
The epoch guard requires either: (a) class-level per-run tracking dict `{entity_id: set[lead_id]}`
in `EventExtractor`, analogous to `_seen_routing_families`; or (b) a threshold comparison only at
epoch multiples (e.g., only at ticks divisible by `belief_stale_ticks`). Option (a) matches the
existing pattern.

### `paid_info_changed_goal` — correlation path

`PaidInformationTransactionSystem.enforce()` (`paid_information.py:75`) creates a
`ResourceTransferIntent(source_kind="INFORMATION_PURCHASE", strategic_upd=StrategicUpdate(
leads_add_or_update=[lead], projects_remove=[seeking_project.id]))`. The contingent
`StrategicUpdate` is embedded in the intent, not directly in `entity_updates`.

After resolution by `ResourceTransactionResolver` (downstream authoritative phase), the
`INFORMATION_SEEKING` project is removed from `entity.strategic.projects`. The entity's
`current_project_id` (`StrategicComponent.current_project_id`, `strategic.py:346`) may also change
if the removed project was active.

**Detection path in EventExtractor**: at the same site as the `paid_information_transaction` emit
(line 322), also check `entity.strategic.current_project_id != prior_ent.strategic.current_project_id`.
If true, emit `paid_info_changed_goal`. Note that the goal-change may also manifest as the projects
dict shrinking: `entity.strategic.projects` has fewer entries than `prior_ent.strategic.projects`
for this entity. The `current_project_id` diff is the simpler and more reliable signal.

**Pipeline ordering concern (ticket open question)**: The EventExtractor runs after the full
StateUpdate is committed to AuthoritativeState. By then, the contingent StrategicUpdate has been
applied. So `entity.strategic.current_project_id` in `current_state` already reflects the post-
purchase state. This means the correlation does NOT require cross-tick state; it is a within-tick
state-diff in a single `extract()` call.

### `decision_diverged_by_belief` — stale belief influencing project choice

`StrategicComponent` has `projects: Dict[str, ProjectState]` and `current_project_id: Optional[str]`.
`ProjectState` has `score: float`. The highest-scoring project can be inferred from
`max(entity.strategic.projects.values(), key=lambda p: p.score)`.

Detection condition:
- Entity has an active project (`current_project_id` is set)
- The active project is NOT the highest-scoring one (score gap > threshold)
- Entity holds at least one lead with `certainty == LeadCertainty.VAGUE`

This maps to the ticket's simplified form: "entity chose non-top project while holding a belief with
certainty < 0.3" — the VAGUE enum value is the proxy for certainty < 0.3.

The `repeat_tip_count` field in InformationScorer.score() for `decision_diverged_by_belief`
(`information.py:133`) expects `payload.get("repeat_tip_count", 0)`. This needs to be computed: how
many times has the entity purchased information on the same subject? This requires cross-referencing
lead history or counting leads with `kind="information"` and the same subject. A first-pass
implementation can omit this and default to 0 (the scorer falls through to `subjective_divergence`).

The `is_collapse` flag requires a population-level check (all entities share identical certainty
distributions). This is not computable in the per-entity loop — it requires a pre-pass over all
entities. For a first implementation this should be emitted separately or skipped.

### `decision_divergence_detected` (COGNITION) — project type vs objective tier

**`ObjectiveTier` does not exist in code**. The concept "entity's top-level strategic objective tier"
is from the scoring contract docs but has no runtime representation. `ProjectKind` (`strategic.py:134`)
has: CRAFTING, QUEST, EXPLORATION, COMBAT, SOCIAL, RECOVERY, PREPARATION, TRAINING, HARVESTING,
INFORMATION, INFORMATION_SEEKING, TRAVEL.

Proposed tier mapping (local to event_extractor):
- SURVIVAL tier: `{COMBAT, RECOVERY, PREPARATION}`
- ECONOMY tier: `{HARVESTING, CRAFTING, INFORMATION, INFORMATION_SEEKING, QUEST}`
- SOCIAL tier: `{SOCIAL, TRAINING, EXPLORATION, TRAVEL}`

Detection: if the active project's tier differs from the highest-scoring non-active project's tier,
emit `decision_divergence_detected`. Payload should include `active_project_kind`,
`top_project_kind`, `active_tier`, `top_tier`.

The `is_collapse` flag in `CognitionScorer.score("decision_divergence_detected")` (cognition.py:95)
requires a population-level check (all entities identical). Omit from first pass; emit `is_collapse=False`
always.

### Can `decision_diverged_by_belief` and `decision_divergence_detected` share an emitter?

They are computed from the same state block (entity.strategic diff) but target different scorers and
carry different payloads. They can share a single code block location in `event_extractor.py` (a
new "Strategic divergence detection" section after the lead-certainty state diff). They emit separate
`SimulationEvent` objects. No shared emitter function is warranted — the detection conditions are
different enough that a common helper would obscure the distinction.

---

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` defines lead certainty laws: leads degrade when their
  target is proved inconsistent, but the certainty levels are ordinal (VAGUE/APPROXIMATE/PRECISE),
  not continuous float. Any band-crossing logic must use ordinal ranks, not float thresholds.
- Engine Contract `kernel.md`: EventExtractor runs in Phase 6 (Persistence), after all authoritative
  mutations are committed. The full prior vs. current state diff is available.
- `authoritative_mutation_pipeline_contract.md`: `PaidInformationTransactionSystem` (PP-26) runs
  before `ResourceTransactionResolver` (PP-27). By the time EventExtractor sees the committed state,
  the contingent StrategicUpdate has been applied. The `paid_info_changed_goal` correlation can be
  done from the within-tick state diff alone.
- All durable mutations in `lead_contradiction.py` are typed updates — the `lead_contradiction_resolved`
  event is purely observational and does not need to change the mutation model.

---

## Parity Ledger Overlap

| Entry | Relevance |
|---|---|
| STRAT-012 | "Knowledge remains uncertain until resolved" — covers LeadState certainty lifecycle; `lead_certainty_updated` band-crossing is a new observability event, not a mechanics change. No status update required. |
| STRAT-008/STRAT-009 | Lead suppression and exhaustion — `lead_contradiction_resolved` is an emit-only addition; parity status `verified` unchanged. |
| No STRAT entry | `lead_certainty_updated` vs `lead_certainty_changed` distinction: no parity entry covers the event emission gap or the scorer payload mismatch. A new `infrastructure.yaml` entry (or STRAT addendum) is needed to track `certainty_delta` payload correctness. |
| No STRAT entry | `belief_stale` detection via `discovered_tick` (no `last_updated_tick`): document as limitation in the ticket's implementation notes; no parity divergence since `LeadState` is correctly implemented — only the observability layer lacks the field reference. |

---

## Prior Work

- `stored_artifacts/TCK-20260629-SIMQ-EMIT-COGNITION/` — established the pattern:
  - All pipeline phases are `@staticmethod`, no `event_recorder` injection; EventExtractor is the
    sole observability path.
  - MagicMock-based unit test pattern in `tests/unit/observability/test_event_extractor_cognition.py`.
  - Confirmed that `intent_results` (not `resource_transfers`) is the correct field to inspect for
    accepted transactions.
- `stored_artifacts/TCK-20260629-SIMQ-EMIT-ECONOMY/` — established dual-emit pattern for INFORMATION_PURCHASE
  (both `paid_information_transaction` and a second economy event from the same intent). The same
  dual-emit approach applies here for `paid_info_changed_goal` when `current_project_id` changes.
- `docs/simulation_quality/event_type_coverage.md §3.2–§3.3` — authoritative gap list; 6 entries to
  be closed by this ticket.

---

## Risks and Open Questions

### Decisions Required

1. **`lead_certainty_updated` vs patching `lead_certainty_changed`**: Should `lead_certainty_updated`
   be emitted AS WELL AS `lead_certainty_changed` (dual emit from state-diff block), or should
   `lead_certainty_changed` be updated to carry `certainty_delta` and `lead_certainty_updated` be a
   separate emit only on band-crossing? Recommendation: dual emit — preserve `lead_certainty_changed`
   unchanged for backward compatibility, add `lead_certainty_updated` as a second emit with `certainty_delta`
   and band metadata. Also fix `lead_certainty_changed` to add `certainty_delta` in its payload (fixes
   the dead CognitionScorer branches as a side effect).

2. **`belief_stale` staleness field**: `LeadState` has no `last_updated_tick`. Staleness must use
   `discovered_tick`. Confirm this is acceptable or require a `LeadState` field addition (out of scope
   per the ticket's out-of-scope section).

3. **`paid_info_changed_goal` trigger**: Is a `current_project_id` change sufficient, or should it
   also require that the new project kind differs from INFORMATION_SEEKING? (The removed project IS
   the INFORMATION_SEEKING project — so the project-kind change is guaranteed if any active project
   change occurs.)

4. **`decision_divergence_detected` tier mapping**: The tier mapping (SURVIVAL/ECONOMY/SOCIAL) is not
   in code. Confirm that a local dict in `event_extractor.py` is acceptable, or require a shared
   module (e.g., `src/simulation_quality/divergence_tiers.py`) to keep it testable.

5. **`is_collapse` population check**: Both `decision_diverged_by_belief` and
   `decision_divergence_detected` scorers have `is_collapse` branches that require population-level
   data not available in the per-entity loop. First pass should emit `is_collapse=False` always and
   leave the collapse detection as a follow-on.

### Other Risks

- **Deduplication of `belief_stale`**: Without a per-run dedup guard (`_seen_stale_leads`), this will
  fire every tick for every stale lead — potentially thousands of events. The class-level pattern from
  `_seen_routing_families` must be replicated.
- **`paid_info_changed_goal` false-positives**: If `current_project_id` changes for a reason other
  than the paid info (e.g., combat interruption in the same tick), the event fires incorrectly. The
  guard should be: INFORMATION_PURCHASE accepted in same tick AND project changed. The conjunction
  reduces but does not eliminate false positives.
- **Scorer payload mismatch carries forward**: If `certainty_delta` is not added to both
  `lead_certainty_changed` and `lead_certainty_updated`, the CognitionScorer branches remain dead.
  This must be fixed in the same commit.

---

## Anti-Drift Hazards

- `LeadState` is frozen (`frozen=True, slots=True`). Do NOT add `last_updated_tick` to fix the stale
  detection — use `discovered_tick`. Adding a field to LeadState requires a schema migration and is
  out of scope.
- `LeadCertainty` has exactly 4 values. Any ordinal rank mapping must handle `EXHAUSTED` explicitly
  (it should not be treated as "high certainty" despite being rank 3 in a naive sort).
- `intent_results` is used (not `resource_transfers`). The prior pass (`TCK-20260629`) confirmed
  `resource_transfers` is cleared by PP-27 before EventExtractor runs — `intent_results` carries
  accepted outcomes. Do not switch to `resource_transfers`.
- `EventExtractor._seen_routing_families` is reset via `reset_run_state()`. Any new per-run tracking
  dict (`_seen_stale_leads`) must also be cleared there.
- `lead_contradiction_resolved` must only emit AFTER the `belief_contradiction` event is already
  appended in the same iteration. Do not split them across the function — they are co-located at
  line 234 in `enforce()`.
