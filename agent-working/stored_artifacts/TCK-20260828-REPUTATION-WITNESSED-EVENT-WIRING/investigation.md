---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
artifact_type: investigation
tags: [social, cognition, progression]
---

# Investigation — TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING

## Context Scan Note

Both mandated Step-0 semantic search tools were attempted before any grep/file read, per Hard Rule:

- `mcp__knowledge-search__search_docs(query="ReputationUpdateService process_witnessed_event witnessed
  event reputation escort betrayal")` → `{"error":"index not found","action":"run make knowledge-index"}`.
  This is the same pre-existing environment gap already logged by the parent investigation
  (`stored_artifacts/TCK-20260824-WIRE-ORPHANED-MECHANISMS/investigation.md`) — confirmed still
  broken, not re-attempted via the `tools/knowledge_search.py` fallback since the orchestrator had
  already supplied a successful `graphify query` result.
- `graphify query "ReputationUpdateService process_witnessed_event QuestKind escort
  CooperationLearningService betrayal"` → succeeded, BFS depth=2, 308 nodes. Seeded the initial
  target list (`ReputationUpdateService`, `QuestKind`, `CooperationLearningService`,
  `CooperationPhase`, `ContractService`, `QuestResolutionSystem`, `WorldCompiler`) confirmed below via
  direct source reads.

All findings below are independently re-verified from source, not restated from the orchestrator's
pre-research uncritically — several findings extend or correct that pre-research (see "Corrections
and additions to the orchestrator's pre-research" at the end of Current Behavior).

## Current Behavior

### ReputationUpdateService — orphaned, zero callers

`ReputationUpdateService.process_witnessed_event(profile, event_kind)` —
`src/domains/commitment/reputation.py:14-27`. Static method, branches on exactly 3 literal strings:
`"successful_escort"` (labels `reliable` +0.1, capped 1.0), `"betrayal"` (`betrayer` +0.4 capped
1.0, `reliable` −0.3 floored 0.0), `"clear_camp"` (`camp_clearer` +0.2, `heroic` +0.1). Returns a
new `PublicReputationProfile` via `dataclasses.replace`; unrecognized `event_kind` is a no-op.
`grep -rn "ReputationUpdateService" src/` → only its own definition and the
`src/domains/commitment/__init__.py:9,15` re-export. Zero callers anywhere — confirmed.

### Durable-state path

`PublicReputationProfile` (`src/core/cognition.py:509-515`) lives at
`entity.cognition.relationships.public_reputation` — nested under `RelationshipModel`
(`src/core/cognition.py:525-538`), itself nested under `CognitionModel.relationships`
(`src/core/cognition.py:545-552`). Not directly `entity.cognition.public_reputation` — the ticket's
own prose is loose here, confirmed via direct read. The only typed authoritative path to mutate it
is whole-bundle replacement via `EntityUpdate.cognition_bundle_set: Optional[Any]`
(`src/core/updates.py:655`), applied in `CognitionPatch` construction
(`src/engine/patches.py:742-743`, `src/engine/apply.py` presumably consumes `CognitionPatch` — not
re-read in full, out of this ticket's direct scope). There is no per-field
`public_reputation_set`/`relationships_set` update type.

### Critical merge-safety hazard — confirmed directly

`MemoryUpdatePhase.apply()` (`src/domains/memory/phase.py:30-53`) runs as pipeline phase
`"memory_update"` at `src/engine/pipeline.py:156`, and **unconditionally** sets
`cognition_bundle_set=new_entity.cognition` for every active/alive entity every tick (line 51),
computed fresh from `entity.cognition` (the live state, not any prior `cognition_bundle_set`
already staged in `update.entity_updates`). `CooperationPhase.execute()`
(`src/domains/cooperation/phase.py`, pipeline phase `"cooperation"`, `src/engine/pipeline.py:189`)
runs after `MemoryUpdatePhase` and currently writes no `cognition_bundle_set` at all (confirmed —
only `social`/`strategic`/`property_updates` fields are touched). `QuestRewardPhase.resolve()`
(pipeline phase `"quest_rewards"`, `src/engine/pipeline.py:319`) and
`NearDeathHardeningPhase.apply()` (pipeline phase `"near_death_hardening"`,
`src/engine/pipeline.py:357`) both run even later, after both `MemoryUpdatePhase` and
`CooperationPhase`.

`EntityUpdate.merge()` (`src/core/updates.py:59-91`, specifically line 91:
`if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] =
other.cognition_bundle_set`) performs a **wholesale replace**, not a deep merge, whenever both
sides set it — so `.merge()` alone does not protect against clobbering.

`NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py:91-99`) is the one
existing precedent that gets this right:

```python
base_cognition = (
    entity_update.cognition_bundle_set
    if entity_update.cognition_bundle_set is not None
    else entity.cognition
)
updated_emotion = EmotionUpdateService.update_on_event(base_cognition.subjective.emotion, "near_death")
new_subjective = replace(base_cognition.subjective, emotion=updated_emotion)
new_cognition = replace(base_cognition, subjective=new_subjective)
```

Any new `cognition_bundle_set` writer inserted at `QuestRewardPhase`/`CooperationPhase` (both run
after `MemoryUpdatePhase`) **must** follow this exact pattern — read `entity_update.cognition_bundle_set`
as the base if already set, never `entity.cognition` directly — or it silently discards
`MemoryUpdatePhase`'s same-tick causal/spatial memory writes for that entity. This hazard is real and
independently confirmed (not just restated from the orchestrator), including confirming
`EntityUpdate.merge()` itself does not protect against it.

### Option 1 — QuestKind.ESCORT — confirmed evidence, with an important count correction

- `src/core/models/quests.py:7-12` — `QuestKind` enum currently has only `HUNT, GATHER, EXPLORE,
  LIBERATE, BOUNTY`. Serialization is by `.name` only
  (`src/api/presenters/state_presenter.py:90`: `q.quest_kind.name if hasattr(...) else str(...)`),
  never the `auto()`-assigned int value — appending `ESCORT` at the end is non-breaking. Confirmed.
- `src/worldbuilding/schema.py:200` — `QuestDefinition.type` is
  `Literal["escort", "hunt", "fetch", "explore", "defend", "investigate"]`. `"escort"` is already a
  legal, authored content-schema value. Confirmed.
- `src/worldbuilding/compiler.py:85-98` — `get_quest_kind(kind_str)` upper-cases and checks
  substring membership for `HUNT`/`GATHER`/`EXPLORE`/`LIBERATE`/`BOUNTY` only; falls through to
  `QuestKind.EXPLORE` for anything else, including `"escort"`, `"fetch"`, `"defend"`,
  `"investigate"`. Confirmed — this is a real, pre-existing content-authoring bug independent of
  this ticket.
- **Correction to the orchestrator's pre-research**: it claimed 2 world modules use
  `type: "escort"`. Direct `grep -n 'type: "escort"' data/content/world_modules/*.yaml` finds **6**:
  `bandit_road_trade_pressure.yaml`, `forest_warden_grove.yaml`, `frontier_village_core.yaml`,
  `orc_clan_territory.yaml`, `orc_clan_territory.yaml`, `settled_quarter.yaml`,
  `trading_company_hub.yaml`. All 6 currently silently compile to `QuestKind.EXPLORE` today. This
  makes the compiler mapping gap a larger, more clearly worth-fixing pre-existing bug than the
  orchestrator's evidence suggested, strengthening (not weakening) the case that fixing it is a
  legitimate, low-risk, evidence-backed side effect of choosing Option 1.
- `src/engine/quests.py::QuestResolutionSystem.enforce()` (lines 154-231) is the real, unconditional
  per-tick phase (`quest_rewards`) that computes
  `is_newly_completed = (updated_quest.quest_status == QuestStatus.COMPLETED and
  project.quest_status == QuestStatus.ACTIVE)` (line 195) with `project` (the pre-update
  `QuestState`, carrying `.quest_kind`) already in scope in the per-quest loop. This is the natural,
  minimal insertion point: `if is_newly_completed and project.quest_kind == QuestKind.ESCORT: ...
  call ReputationUpdateService.process_witnessed_event(entity's public_reputation, "successful_escort")`.
- **Confirmed systemic blocker, independently re-verified**: `grep -n
  "target_archetype_id\|target_faction_id\|target_kind\|target_pos\|target_position\|target_region_id"
  src/worldbuilding/compiler.py` → zero results. The static content compiler never populates ANY
  quest-progress-driving target metadata for ANY `QuestKind` compiled from `world_modules/*.yaml` —
  not just ESCORT. This means a compiled ESCORT quest, even after fixing the compiler mapping bug
  above, still has no live driver moving it toward `is_newly_completed` via the static-content path.
  This is a separate, systemic, pre-existing gap affecting all 5 existing kinds equally — confirmed,
  not introduced or fixable by this ticket.
- The procedural quest generator (`src/quests/generator.py`, `QUEST_TEMPLATES` at
  `src/quests/templates.py:15`) does populate real target metadata (`target_kind` for HUNT,
  presumably `target_pos` for EXPLORE — not fully re-read) for its own fixed template set, but that
  set only covers the 5 existing `QuestKind` values; no `ESCORT` template exists.
  `PRESSURE_AFFINITY` similarly only maps existing kinds. Adding an ESCORT template is new gameplay
  content scope, correctly identified as disproportionate to this ticket.
- **Additional finding, not in the orchestrator's pre-research**: the Mechanics Bible already
  documents a *different*, unrelated "escort" mechanism — `docs/mechanics/04_strategic_cognition.md`
  §6.9 "Escort Route Scoring (SOC-230)", gated on `GroupState.escort_target_id`
  (`src/core/state.py:568`), read at `src/domains/adventure/scoring.py:358-363`. Checked whether
  this could be a cleaner "escort" detection site than `QuestKind.ESCORT`:
  `grep -rn "escort_target_id\s*=" src/` (excluding the field definition and read comparisons) →
  **zero write sites anywhere**. `escort_target_id` is never set by any code in this repo — it is
  itself a dead/unpopulated field, read-only logic gated on a value nothing ever assigns. This rules
  out a third "use the existing route-scoring escort concept" option — there is no live "escort in
  progress" or "escort completed" signal anywhere in the codebase today via any mechanism, not just
  `QuestKind`.
- **Precedent for accepting "wired but practically unreachable pending a separate gap"**: the parent
  investigation (`stored_artifacts/TCK-20260824-WIRE-ORPHANED-MECHANISMS/investigation.md`, §3)
  explicitly accepted `BuildingSabotageSystem` as sufficiently "real" and wired despite it being
  "currently unreachable in practice from any AI decision path... a distinct gap from this ticket's
  scope." Option 1 is structurally identical: a real enum value + a real, narrowly-scoped compiler
  bugfix + a real per-tick pipeline call site, blocked only by a separate, systemic, already
  pre-existing, explicitly out-of-scope upstream gap (quest-progress metadata population, which
  affects all 5 pre-existing `QuestKind` values equally, not something this ticket creates). This
  reasoning is judged sound on independent re-verification.

### Option 2 — CooperationLearningService betrayal branch — confirmed evidence

- `src/domains/cooperation/services.py:329-362` — `CooperationLearningService.learn()`. `out_type ==
  "betrayal"` branch (line 352-355): `trust_delta=-0.75, grudge_delta=0.9, pref_mod=0.0`.
  `out_type == "abandoned"` branch (line 348-351): `trust_delta=-0.25, grudge_delta=0.3,
  pref_mod=0.4`.
- `CooperationLearningService` is imported into `CooperationPhase`
  (`src/domains/cooperation/phase.py:19`) but `grep -n "CooperationLearningService\."
  src/domains/cooperation/phase.py` → zero matches. Confirmed dead: imported, never called.
- `CooperationPhase.execute()` (`src/domains/cooperation/phase.py:34-173`) does run live,
  unconditionally, every tick for every active entity/group — a genuinely stronger production
  footing than the quest-content pipeline (which is blocked on the systemic metadata gap above).
- `PartyCohesionService.evaluate()` (`src/domains/cooperation/services.py:261-313`) computes
  `"MEMBER_ABANDONING"`/`"LEADER_LOST"` (among `STABLE`/`NEEDS_REGROUP`), and
  `CooperationPhase.execute()` (lines 143-160) already **acts** on `MEMBER_ABANDONING`/`LEADER_LOST`
  by decrementing trust by a flat `-0.25` for every remaining party member toward the leader —
  matching `CooperationLearningService.learn()`'s `"abandoned"` branch magnitude (`-0.25`) exactly,
  not its `"betrayal"` branch (`-0.75`). Confirmed by direct read of both files.
- No genuinely distinct "betrayal" (as opposed to "abandonment") detection condition exists anywhere
  live in the codebase today. Also checked `ContractService.resolve_contract_outcome`'s
  `betrayal: bool = False` parameter (`src/systems/social_systems/contracts.py:181-252`) — `grep -rn
  "resolve_contract_outcome" src/` shows exactly one real caller
  (`src/systems/social_systems/contracts.py:276`, always `success=True`, `betrayal` never passed —
  defaults to `False`). `grep -rn "betrayal=True" src/` → exactly one hit, and it is unrelated:
  `src/domains/commitment/abandonment.py:48`, inside `AbandonmentEvaluator.evaluate_abandonment()`'s
  own internal `GREEDY_DESERTION` branch construction (`is_betrayal=True`), not a caller passing
  `betrayal=True` into `ContractService`.
- **Additional finding, not in the orchestrator's pre-research**: `AbandonmentEvaluator` itself
  (`src/domains/commitment/abandonment.py`) *does* have 2 real callers —
  `src/observability/event_extractor.py:1125` and `src/observability/event_shapers.py:1816` — both
  reachable from live code, contradicting a naive "AbandonmentEvaluator is orphaned" assumption.
  However, both call sites hardcode `is_party_in_combat=False, is_greed_driven=False` (with an
  in-code comment "Q1: default; see plan decisions" at both sites), meaning
  `evaluate_abandonment()` can **never** actually return `GREEDY_DESERTION`/`is_betrayal=True` from
  either live call site today — only `SURVIVAL` or `VOLUNTARY_QUIT` are reachable. Additionally,
  both call sites live in `src/observability/` (event extraction/shaping for telemetry and read
  models), not the authoritative decision/mutation pipeline — even if `is_greed_driven` became
  reachable, this is the wrong architectural layer to trigger a durable `ReputationUpdateService`
  mutation from (observability is downstream/read-only per this repo's layering). This closes off a
  third candidate the orchestrator's pre-research did not consider and confirms its core claim even
  more strongly: **no genuinely live, reachable, authoritative "betrayal" detection condition exists
  anywhere in this codebase today**, across all three places betrayal-flavored logic exists
  (`CooperationLearningService`, `ContractService`, `AbandonmentEvaluator`).
- Using `CooperationLearningService`'s betrayal branch for this ticket would therefore require
  inventing new domain logic to distinguish "betrayal" from "abandonment" (e.g., a new condition on
  `PartyCohesionService.evaluate()` or a new signal entirely) — genuinely new, ungrounded
  domain-modeling work, not a call-site insertion, exactly as the ticket's own Request Summary
  states.

## Mechanics / Engine Constraints

- **Durable State Rule / Authoritative Application** (CLAUDE.md Architecture Rule; `docs/core/state.md`
  immutability law): the wiring must route through `EntityUpdate.cognition_bundle_set`
  (`src/core/updates.py:655`), applied via `CognitionPatch` (`src/engine/patches.py:742-743`) — the
  only typed path back into `entity.cognition`. No per-field update type exists for
  `relationships`/`public_reputation`; using the whole-bundle replace is the only architecturally
  sound option today, following the `NearDeathHardeningPhase.apply()` merge-safe precedent described
  above (read `entity_update.cognition_bundle_set` as base if already set, never `entity.cognition`
  directly, given both candidate insertion phases run after `MemoryUpdatePhase`).
- **docs/mechanics/04_strategic_cognition.md §6.9** ("Escort Route Scoring", SOC-230) governs a
  distinct, unrelated escort mechanism (`GroupState.escort_target_id`-driven route scoring, not
  `QuestKind`). It is not itself a blocker or an available detection site (its field is never
  written anywhere, see above) but establishes that "escort" as a concept already has one live
  (route-scoring bias) and one dormant (`escort_target_id` never set) presence in the Mechanics
  Bible — worth being aware of so the new `QuestKind.ESCORT` mechanism (if chosen) is understood as
  additive to, not a replacement or conflict with, §6.9.
- **docs/simulation/domains/commitment_contract.md** (already read as required input) documents
  `ReputationUpdateService.process_witnessed_event()`'s exact label-delta table (lines 118-128) and
  explicitly states in its "What It May Mutate" section (lines 155-161): "the caller is responsible
  for writing the updated profile back into the entity's cognition state... Verify at integration
  point whether the caller routes this through the authoritative pipeline or applies it as a direct
  replace." This ticket's implementation must route through the authoritative
  `cognition_bundle_set` path, satisfying that doc's own stated expectation.
- **No formula/law constraint from docs/mechanics/ blocks either option.** Quest completion mechanics
  (`QuestResolutionSystem.enforce()`) and cooperation mechanics (`CooperationPhase`) are both already
  governed by existing, unmodified logic; this ticket only adds a reputation side-effect at an
  existing detection point (Option 1) or requires inventing new detection logic not covered by any
  existing Mechanics Bible chapter (Option 2).

## Docs Requiring Update

- `docs/parity_ledger/social_narrative.yaml`: no `ReputationUpdateService`/`process_witnessed_event`
  entry exists anywhere in this file (confirmed: `grep -n -i "ReputationUpdateService\|
  process_witnessed_event\|PublicReputationProfile" docs/parity_ledger/*.yaml` → zero results across
  all parity files). A new entry is required once this ticket wires a real call site — see Parity
  Ledger Overlap below for the exact next-available ID.
- `docs/simulation/domains/commitment_contract.md`: the "Engine Pipeline Phase" section (line 44,
  "Engine event handlers — call `ReputationUpdateService.process_witnessed_event()` when a social
  event is witnessed") and the "Domain Interactions" table (line 185, same phrasing) currently
  describe an aspirational/target-state call site in generic language ("Engine event handlers").
  Once this ticket lands, this generic phrasing becomes inaccurate in a way it currently is not (it
  currently reads as forward-looking; after landing, a reader would reasonably expect it to name the
  real site). It should be updated to cite the concrete file:line of whichever call site is chosen
  (e.g. `QuestResolutionSystem.enforce()` at `src/engine/quests.py` if Option 1 is chosen), matching
  how `NearDeathHardeningPhase.apply()`'s docstring already names its own real call site precisely.

The following docs were considered and are **not** required to change as part of this ticket
(Format 2 — prose only, no leading bullet):

`docs/mechanics/04_strategic_cognition.md`'s §6.9 "Escort Route Scoring" section (path:
`docs/mechanics/04_strategic_cognition.md`) does not need to change: it documents the unrelated
`GroupState.escort_target_id`-driven route-scoring mechanism, not `QuestKind`/`ReputationUpdateService`,
and this ticket does not touch `escort_target_id` or `AdventureRouteScorer`.

`docs/simulation/social_systems_contract.md`'s "Contracts" section (path:
`docs/simulation/social_systems_contract.md`) describes an `ESCORT` `ContractKind` whose breach
triggers `ReputationUpdateService` — but the real `ContractKind` enum
(`src/core/strategic.py:73-85`) has no `ESCORT` value (only `RECRUITMENT, LOAN, PROTECTION,
MERCHANT, POSITION_SWAP, TEAM_UP, PAID_INFORMATION`), confirmed by direct read. This section is
stale/aspirational, matching the pattern the parent investigation already established for
`commitment_contract.md`/`emotion_contract.md` describing target state ahead of code. It is not
required reading for this ticket's specific scope (neither candidate option touches `ContractKind`
or contract breach logic) and fixing it is a separate pre-existing-drift cleanup, not caused by or
required for this ticket.

`docs/simulation/social_systems_contract.md`'s "Reputation" section (path:
`docs/simulation/social_systems_contract.md`, same file, different section — reputation table at
lines 172-182) is also independently found to be inaccurate: it states deltas ("escort completed:
reputation +0.1, RELIABLE label added"; "betrayal witnessed: reputation −0.2, BETRAYER label
added"; "camp cleared: reputation +0.05, COMBATANT label added") and label names
(`RELIABLE`/`BETRAYER`/`COMBATANT`, uppercase) that do not match the real code in
`src/domains/commitment/reputation.py` (`reliable`/`betrayer`/`camp_clearer`/`heroic`, lowercase,
with different delta magnitudes — e.g. betrayal is `betrayer +0.4, reliable -0.3` in code, not "−0.2
BETRAYER" as the doc states). This is pre-existing drift unrelated to this ticket's scope — the
ticket does not change label names or delta magnitudes, only wires a real call site — so fixing it
here would be scope creep beyond the Acceptance Criteria. Flagged instead as a Risk/anti-drift note
below for a future doc-cleanup ticket.

## Parity Ledger Overlap

- **No existing entries** for `ReputationUpdateService`/`process_witnessed_event`/
  `PublicReputationProfile` anywhere in `docs/parity_ledger/` — confirmed via direct grep across all
  files, matching the ticket's own premise. A **new** entry is required, not a status update.
- `docs/parity_ledger/social_narrative.yaml` currently has 272 entries; the highest existing numeric
  ID is `SOC-251` (confirmed via `grep -o "id: SOC-[0-9]*" docs/parity_ledger/social_narrative.yaml
  | sed 's/id: SOC-//' | sort -n | tail -1`). **Next available ID: `SOC-252`.**
- No P0 entries are implicated by either option's wiring (neither `QuestResolutionSystem.enforce()`
  nor `CooperationPhase.execute()` has any existing P0 parity entry that this change would touch),
  but the ticket's own Acceptance Criteria independently demand "a parity ledger entry exists for
  this mechanism with a passing `test_path`" regardless of priority — this is a ticket-level
  requirement, not a P0 ledger-level one. Recommend `priority: P1`, matching the priority level of
  the other `docs/simulation/domains/commitment_contract.md`-governed mechanisms
  (`CommitmentPressureService`, `AbandonmentEvaluator` — both P1 in their own doc's framing) rather
  than `P0`, since this is a reputation side-effect layer, not a core state-integrity law.

## Prior Work

- `stored_artifacts/TCK-20260824-WIRE-ORPHANED-MECHANISMS/investigation.md` §5 — the direct parent
  investigation this ticket was split out of. Its atomicity table rated item 5
  (`ReputationUpdateService`) "High" risk with "no clean existing site for any of its 3 event kinds"
  and recommended a dedicated child ticket "scoped down to whatever event-kind mapping planning
  decides is realistic, possibly re-scoping away from the 3 literal strings if no real event exists
  for them" — exactly the situation this investigation confirms remains true, with the added
  confirmation that a third possible detection site (`AbandonmentEvaluator`'s live observability
  callers) is also unreachable for betrayal specifically.
- `tickets/done/TCK-20260618-AUDIT-D11-DEAD` — likely origin audit that first flagged this and the
  other 6 orphaned mechanisms; not re-read in full (per the parent investigation's own note that it
  independently re-verified every claim from source rather than relying on this audit).
- No other `stored_artifacts/`/`tickets/done/` entries reference `ReputationUpdateService`,
  `PublicReputationProfile`, `CooperationLearningService`, or `QuestKind.ESCORT` — checked via
  `grep -rl` across both directories.

## Risks and Open Questions

1. **Central open question, not resolved by this investigation per the ticket's own Assumptions
   section**: which of Option 1 (`QuestKind.ESCORT`) or Option 2 (`CooperationLearningService`
   betrayal activation) to implement. This investigation's recommendation (see below) is evidence-backed
   but is explicitly a planning decision for the Plan phase to make and document, not something to
   silently assume.
   - **Recommendation: Option 1 (`QuestKind.ESCORT`)**, for the following reasons, weighed against
     Option 2:
     - Option 1's full change set (add enum value, fix `get_quest_kind()`'s substring mapping, add
       one conditional branch in `QuestResolutionSystem.enforce()`) is a genuine call-site insertion
       plus a narrowly-scoped, well-evidenced bugfix (6 real world-content files already author
       `type: "escort"` and are currently silently miscompiled to EXPLORE) — it does not require
       inventing new domain semantics.
     - Option 2 requires inventing a new way to distinguish "betrayal" from "abandonment" that does
       not exist anywhere in the live codebase today (confirmed across all three betrayal-adjacent
       code paths: `CooperationLearningService`, `ContractService`, `AbandonmentEvaluator`) — this is
       new, ungrounded domain-modeling work, explicitly heavier and riskier than a call-site
       insertion, and the ticket's own Request Summary already flags this distinction.
     - Both options share the same "wired to a real per-tick phase, but not fully end-to-end
       reachable in practice" caveat once fully traced: Option 1 is blocked by the separate,
       out-of-scope, systemic quest-metadata-population gap; Option 2 (if implemented as a narrow
       call-site insertion without new betrayal-detection logic) would only be reachable by
       reusing the abandonment magnitude, which would be a **mislabeling** (an abandonment event
       reported as "betrayal"), not merely an unreachability gap — this is qualitatively worse than
       Option 1's caveat, because it produces semantically wrong behavior when it *does* fire, not
       just no behavior. Given the parent ticket's own precedent (`BuildingSabotageSystem`) already
       accepts "wired but not yet reachable" as sufficient, Option 1's caveat is the acceptable kind;
       Option 2's is not, unless genuinely new betrayal-detection logic is built (out of this
       ticket's minimum viable scope per its own Assumptions).
   - If Plan disagrees and selects Option 2, it must explicitly design and document the new
     betrayal-detection condition (not just insert the call) — this investigation does not supply
     that design, per the Uncertainty Rule ("vague leads stay vague until evidence narrows them").
2. **Option 1's completion path is currently unreachable end-to-end** for any world-content-authored
   ESCORT quest, because of the separate, systemic, pre-existing compiler gap (no quest ever gets
   `target_*` metadata populated from static content, for any `QuestKind`). This must be documented
   explicitly in the Plan/ticket rather than silently left implicit — the wiring will be real and
   correct, but will not visibly fire in a live simulation run until that separate gap is fixed by a
   future, out-of-scope ticket. Confirmed this is not something this ticket can or should absorb (it
   affects all 5 pre-existing `QuestKind` values equally, not just ESCORT).
3. **`clear_camp` event kind remains explicitly out of scope** per the ticket's own Out of Scope
   section — no existing quest-kind or event constant matches it today; confirmed no additional
   evidence surfaced during this investigation that would change that.
4. **Pre-existing doc drift in `docs/simulation/social_systems_contract.md`'s Reputation section**
   (wrong label names/deltas, and a stale `ESCORT ContractKind` reference in Contracts) is real but
   out of this ticket's scope to fix — flagged for a future doc-cleanup ticket, not silently folded
   into this one's Docs Requiring Update (see Format-2 note above).

## Anti-Drift Hazards

- **Any new `cognition_bundle_set` writer must read `entity_update.cognition_bundle_set` as its
  base (falling back to `entity.cognition` only if unset), never `entity.cognition` directly** —
  both candidate insertion points (`QuestRewardPhase`/`quest_rewards` and, if Option 2 were chosen,
  `CooperationPhase`/`cooperation`) run after `MemoryUpdatePhase`/`memory_update`, which
  unconditionally writes `cognition_bundle_set` for every active entity every tick. Skipping this
  merge-safe pattern silently discards that tick's causal/spatial memory writes for the same entity.
  Follow `NearDeathHardeningPhase.apply()`'s exact pattern
  (`src/engine/pipeline_phases/hardening.py:91-99`).
- **Do not wire `CooperationLearningService.learn()`'s betrayal branch to the existing
  `MEMBER_ABANDONING`/`-0.25` trust-decrement site in `CooperationPhase.execute()` (lines 143-160)
  without adding genuine new distinguishing logic.** That site's magnitude and triggering conditions
  already match `learn()`'s `"abandoned"` branch, not `"betrayal"` — routing it to
  `ReputationUpdateService.process_witnessed_event(profile, "betrayal")` as-is would mislabel every
  ordinary party-abandonment event as a witnessed betrayal, silently making the `betrayer` label far
  more common than intended and skewing `apply_partner_fit_bias()`'s 2× betrayal-weight filtering
  (`docs/simulation/domains/commitment_contract.md` lines 102-116) for reasons unrelated to actual
  betrayal.
- **Do not conflate this ticket's `QuestKind.ESCORT` (if chosen) with
  `docs/mechanics/04_strategic_cognition.md` §6.9's `GroupState.escort_target_id`-driven route
  scoring** — they are two independent "escort" concepts. Do not attempt to wire
  `ReputationUpdateService` off `escort_target_id` state changes; that field is never written
  anywhere and doing so would be new, unscoped domain logic beyond this ticket.
- **Do not touch `ReputationService` (`src/systems/social_systems/reputation.py`)** — explicitly out
  of scope per the ticket; confirmed still a separately orphaned, zero-caller class, unrelated to
  `ReputationUpdateService`.
- **Do not "fix" the compiler's missing `target_*` metadata population as part of this ticket** —
  confirmed systemic and pre-existing, affecting all 5 current `QuestKind` values, explicitly a
  separate gap per the parent investigation's precedent-setting treatment of the analogous
  `BuildingSabotageSystem` case.
- **If Option 1 is chosen, do not silently expand the compiler-mapping fix beyond `"escort"`.** The
  compiler's `get_quest_kind()` also silently mishandles `"fetch"`, `"defend"`, `"investigate"`
  (falls through to EXPLORE for all of them) — fixing only the `"escort"` branch, consistent with
  this ticket's Scope, and leaving the other 3 literal's mishandling for a separate ticket, avoids
  scope creep while still being an honest, minimal, evidence-backed fix.
