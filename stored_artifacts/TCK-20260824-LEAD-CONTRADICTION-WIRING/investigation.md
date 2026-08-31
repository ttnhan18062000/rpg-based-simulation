---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-LEAD-CONTRADICTION-WIRING
artifact_type: investigation
tags: [information, strategy, cognition]
---

# Investigation — TCK-20260824-LEAD-CONTRADICTION-WIRING

## Current Behavior

### 1. `LeadContradictionSystem.enforce()` is never called from `pipeline.refine()`
`src/engine/pipeline_phases/lead_contradiction.py:99-270` — `LeadContradictionSystem.enforce(state, update)` is a
correctly-written, self-contained decision phase: it scans entities/leads in sorted order (determinism), emits
typed `StrategicUpdate`/`EntityUpdate` mutations (merged via `.merge()`, `dataclasses.replace()` — never a
direct write), decrements provider `reliability_score`, regenerates an `UnknownFact`, and emits
`belief_contradiction` + `lead_contradiction_resolved` `SimulationEvent`s. It follows the exact `run_phase()`
call signature used elsewhere in `pipeline.py` (`state, update -> (StateUpdate, List[SimulationEvent])` pattern
is not used verbatim by `run_phase` — see Risk below on adapting the return shape).

Confirmed via `grep -rln "LeadContradictionSystem"`: the **only** two files that reference the class are
`src/engine/pipeline_phases/lead_contradiction.py` itself and
`tests/unit/cognition/test_information_seeking.py`. There is no call site anywhere in `src/engine/pipeline.py`
or any other production module. It is fully implemented, fully unit-tested in isolation, and never executed by
a real simulation tick.

### 2. `AuthoritativeApplyPipeline.refine()` — exact current phase list (post `CAUSAL-MEMORY-ROUTE-SCORING`)
`src/engine/pipeline.py:41-396`. The docstring at line 46 says "17 distinct phases" — this is stale; the real
count (verified against `docs/engine/authoritative_pipeline.md`'s own "38 Phases" table, which is currently
**in sync** with the code) is **38** `run_phase()` calls, in this exact order:

1. `trust_boundary` 2. `actor_validity` 3. `memory_update` (new since `CAUSAL-MEMORY-ROUTE-SCORING`,
line 154-158) 4. `self_model` 5. `information_belief` 6. `information_intent_execution` 7. `cooperation`
8. `contracts` 9. `blacksmith` 10. `faction_awareness` 11. `diplomatic_transitions` 12. `military_conflict`
13. `action_routing` 14. `position_swaps` 15. `movement_routing` 16. `combat_engagement`
17. `interaction_routing` 18. `interaction_enforcement` 19. `building_sabotage` 20. `town_resolution`
21. `gold_sink` 22. `world_dynamics` 23. `world_emergence` 24. `quest_rewards` 25. `guild_visit` 26. `shop`
27. `paid_information` 28. `resource_transactions` 29. `evolution` 30. `progression_conversion`
31. `strategic_intelligence` 32. `near_death_hardening` 33. `occupancy_resolution` 34. `lifecycle`
35. `groups` 36. `active_contracts` 37. `expired_offers` 38. `capacity_enforcement`.

**Recommended insertion point: immediately after `strategic_intelligence` (#31), before `near_death_hardening`
(#32)** — i.e. inside the existing `# --- Phase 7: Cognitive & Final Integrity ---` group
(`src/engine/pipeline.py:346-370`):

```python
update = run_phase("strategic_intelligence", update, lambda u: StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))
update = run_phase("lead_contradiction", update, lambda u: AuthoritativeApplyPipeline._enforce_lead_contradiction(state, u), "ENABLE_LEAD_CONTRADICTION")
update = run_phase("near_death_hardening", update, lambda u: AuthoritativeApplyPipeline._apply_near_death_hardening(state, u))
```

Rationale:
- `_is_lead_contradicted()` (see §3 below) only reads `state.resource_nodes` / `state.entities` — the frozen,
  pre-tick `AuthoritativeState` snapshot — never the in-flight `update`. Like `memory_update`'s and
  `faction_awareness`'s documented one-tick lag (`pipeline.py:140-144`, `:205-206`), a resource depleted or an
  entity killed *this* tick is only visible to `_is_lead_contradicted()` starting *next* tick, regardless of
  where in `refine()` the phase runs. So phase order does not change correctness of the contradiction check
  itself.
- What phase order *does* affect is which `EntityUpdate.strategic` / `.self_model_bundle_set` writes land last.
  `strategic_intelligence` (`StrategicIntelligenceSystem.fused_strategic_pass`, called via
  `src/systems/strategic_systems/intelligence.py`) is the tick's authoritative owner of lead
  add/remove/suppress logic (confirmed reading `intelligence.py:405-438`: it already runs its own, separate,
  narrower contradiction check — see §"Adjacent System" below — and writes `EntityUpdate.strategic` via
  `existing_ent_upd... replace(...)`, i.e. it **merges**, not replaces). Running `lead_contradiction` right
  after it means `LeadContradictionSystem.enforce()` sees the tick's final lead set (post-suppression) as its
  `state.entities[...].strategic.leads` input via `update.entity_updates`, and its own writes are the last
  strategic-state opinion before the finalize/lifecycle phases. Its own `.merge()` pattern
  (`lead_contradiction.py:186-195`) is safe to run in either position relative to `strategic_intelligence`
  (neither side does a destructive whole-`EntityUpdate` replace, unlike the `CombatEngagementPhase` bug
  documented at `pipeline.py:266-276`), but grouping it with the other "final integrity" phases keeps the
  phase-grouping convention intact and keeps the newest lead-state opinion closest to persistence.
- A new `ENABLE_LEAD_CONTRADICTION` feature flag (à la `ENABLE_MEMORY_UPDATE`, `ENABLE_COMBAT_ENGAGEMENT`) is
  recommended so this can ship SHADOW-mode first, consistent with every other Enhanced-RPG phase added to this
  pipeline; `PhaseDependencyGraph.should_run_phase()` also needs a no-op/always-run entry for the new phase name
  (check `src/engine/phase_graph.py` before implementation — not read in this investigation, flagged as an
  open item below).

### 3. `_is_lead_contradicted()` — exact current logic and the LeadKind mismatch
`src/engine/pipeline_phases/lead_contradiction.py:43-96`.

Real `LeadKind(str, Enum)` members (`src/core/strategic.py:42-56`):
```
LOCATION = "location"
OBJECT   = "object"
EVENT    = "event"
PERSON   = "person"
CONCEPT  = "concept"
```

Current string literals checked by `_is_lead_contradicted()`: `"resource"`, `"location"`, `"person"`,
`"information"`.

- `"location"` → **real** (`LeadKind.LOCATION`).
- `"person"` → **real** (`LeadKind.PERSON`).
- `"resource"` → **NOT a real `LeadKind` value.** No production call site ever constructs a `LeadState` with
  `kind="resource"` (confirmed via `grep -rn "LeadState(" src/` across all 8 production construction sites:
  `src/world/providers/information.py`, `src/domains/information/normalizer.py` (×2),
  `src/town/guild.py`, `src/systems/strategic_systems/belief.py` (×2), `src/engine/pipeline_phases/
  paid_information.py`, `src/strategy/leads.py` — all use `kind="location"` or `kind="information"` or pass
  through an existing `lead.kind`). This branch (`lead_contradiction.py:63-69`) is dead code today.
- `"information"` → **NOT a real `LeadKind` value either**, but it *is* actually produced in production:
  `src/engine/pipeline_phases/paid_information.py:139` constructs `LeadState(..., kind="information", ...)`.
  The `_is_lead_contradicted()` branch for `"information"` (`lead_contradiction.py:90-94`) is an intentional
  no-op ("not validated against world state here"), so this is a real-but-deliberately-unchecked kind, not a
  bug — but it is also not one of the 5 real `LeadKind` enum members, so it sits outside the formal
  classification entirely. Treat as a pre-existing, out-of-ticket-scope naming quirk (paid-information leads
  predate the `LeadKind` enum migration, E42E) — flagged, not fixed, per Out of Scope.

So exactly 2 of the 4 literals (`"resource"`, `"information"`) are not real `LeadKind` values, matching the
ticket's claim, but for different reasons each: `"resource"` is simply dead/unreachable, `"information"` is
real production data deliberately left unchecked.

**Required extension for AC3** (`OBJECT` / `CONCEPT` / `EVENT` coverage): none of the 3 have *any* branch
today — they fall through to `return False` (never contradicted) at `lead_contradiction.py:96`. Per
`docs/simulation/domains/information_contract.md:85-96` and `src/engine/domain/lead_routing.py:33-63`
(`LeadRoutingSystem.resolve_objective_kind`, confirmed wired into production via
`src/systems/strategic_systems/detour.py`), `OBJECT`/`EVENT` leads already route to `ObjectiveKind.INVESTIGATE`
(target = `lead.subject`) and `CONCEPT` leads already route to `ObjectiveKind.ASK_INFORMATION` (target =
`lead.subject`, a domain string like `"alchemy_recipe"`). This means entities can and do pursue OBJECT/EVENT/
CONCEPT leads in production today, but once pursued and found false there is no mechanism to ever mark them
`EXHAUSTED` — they can never leave `strat.leads` other than via profile bandwidth eviction
(`DetourSuggestionSystem.enforce_bandwidth`, STRAT-006), which is not the same as a tested-and-failed outcome
and does not trigger the `UnknownFact`/replanning path. This is a real, live gap, not theoretical:
- `OBJECT`: no natural world-state check exists yet (no ground-truth "does this item exist at this location"
  table is read anywhere in `_is_lead_contradicted()`'s current scope — `state.ground_items` /
  `state.chests` would need to be checked against `lead.subject`/`lead.detail`, similar to the `resource_nodes`
  pattern used for `LOCATION`).
- `EVENT`: `state.recent_world_events` / `state.local_scars` are the closest existing state surfaces (see
  `docs/mechanics/05_world_evolution.md` for regional trauma/calamity state) — an EVENT lead should
  plausibly be tested against whether the referenced world event/scar is still active, but this investigation
  did not find an existing helper for "is this event still true"; a first pass may need to treat EVENT leads
  conservatively (e.g. contradict only when the referenced region no longer has any matching scar/event
  record) — **open question, not resolved here**, see Risks.
- `CONCEPT`: contradiction is naturally tied to a failed `PaidInformationTransactionSystem` query outcome
  (`ObjectiveKind.ASK_INFORMATION` → provider interaction) rather than a `state.<registry>` scan; this is
  closer in shape to what `BeliefContradictionService.detect()` already does (observation-driven, not a
  per-tick state scan) than to `_is_lead_contradicted()`'s existing resource/person branches. Implementer
  should decide whether CONCEPT contradiction belongs in `_is_lead_contradicted()` (state-scan) or is instead
  the natural first real caller of `BeliefContradictionService.detect()` for a `claim_failed_search`-shaped
  observation keyed on domain string instead of resource subject — **open design question, flagged, not
  assumed**.

### 4. `BeliefContradictionService.detect()` — no production call site exists at all
`src/domains/information/contradiction.py:26-76`. `grep -rln "BeliefContradictionService"` across all of
`src/` returns only `contradiction.py` itself — `lead_contradiction.py` does not import or call it (only
mentions it in a comment, line 93). All real callers are test files
(`tests/unit/domains/information/test_phase5_belief_contradiction.py`,
`test_phase5_information_events.py`, `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`
constructs it indirectly). `.detect()` is a fully orphaned static method today.

**The natural call site is `ObservationBeliefBridge.process_observation()`**
(`src/domains/information/bridge.py:22-56`) — it already special-cases `obs_kind == "claim_failed_search"`
(line 45-50) to build a `CONTRADICTION`-shaped `InformationAssimilationResult`, but it does this by hand
(constructing a raw dict and routing straight to `InformationResponseNormalizer.normalize()` +
`InformationAssimilationService.assimilate()`), **without ever calling `BeliefContradictionService.detect()`**.
It also does not handle `region_danger_seen` at all today (only `claim_failed_search`).

**However, `ObservationBeliefBridge.process_observation()` itself has no production caller either** —
`grep -rn "process_observation"` shows only: `bridge.py` (definition), `test_phase5_observation_belief_bridge.py`,
`test_phase5_information_belief_scenarios.py` (both tests), plus an unrelated same-named method on a different
class, `BeliefCycleSystem.process_observation` (`src/systems/strategic_systems/belief.py:117`, called from
production at `src/systems/strategic_systems/intelligence.py:418` — see "Adjacent System" below). So the bridge
that the ticket's scope note points at is *also* dead code — this ticket needs to both (a) give
`ObservationBeliefBridge.process_observation` (or an equivalent inline call) a real caller, and (b) make that
call path invoke `BeliefContradictionService.detect()`.

The only per-tick phase that currently processes anything resembling "an observation" is
`InformationBeliefPhase.apply()` (`src/domains/information/phase.py:28-99`, wired at `pipeline.py:167-174` as
the `information_belief` phase, #5). It currently has exactly two branches: (1) assimilate `pending_responses`
(query answers), (2) route a new query for the first unresolved `UnknownFact`. **Neither branch processes
`claim_failed_search`/`region_danger_seen`-shaped observation events** — those are a third, currently
nonexistent, input channel. Where do such observation dicts get produced today? None do —
`grep -rn "claim_failed_search\|region_danger_seen"` across `src/` returns matches only inside
`contradiction.py` and `bridge.py` themselves (the consumers), never a producer. Building the actual
observation-event *source* (e.g. from a failed harvest/search action outcome, or from perception detecting a
dangerous region) is implicitly required by AC2 ("invoked when a claim_failed_search/region_danger_seen
observation is processed") but is not itself explicitly scoped — **flagged as an open question**: does this
ticket need to also synthesize these observation events from an existing action-outcome signal (e.g.
`ActionRoutingPhase`'s `INVESTIGATE`/harvest-failure outcomes, or `NavigationUpdate.last_failure_reason`), or
is a new `InformationBeliefPhase.apply()` branch that reads a `pending_observation_events` list (mirroring the
existing `pending_information_responses` pattern) sufficient, deferring "who populates that list" to a future
ticket? The safest AC-satisfying interpretation is the latter (add the plumbing + one real synthetic source),
but this should be confirmed at planning time, not assumed here.

**How the result must be applied**: `BeliefContradictionResult` (`contradiction.py:17-23`) is a bare dataclass,
not a `StrategicUpdate`. The call site must translate a `contradiction_detected=True` result into a
`StrategicUpdate(leads_add_or_update=[replace(lead, certainty=result.new_certainty, tested=True,
test_outcome="FAILURE", failure_count=lead.failure_count+1)])`, mirroring exactly what
`LeadContradictionSystem.enforce()` already does at `lead_contradiction.py:152-159` — never a direct mutation
of `entity.strategic.leads`. `InformationBeliefPhase.apply()` already has the merge machinery
(`entity_updates[actor.id] = EntityUpdate(..., strategic=..., self_model_bundle_set=...)`) to plug this into.

### 5. Adjacent system: `BeliefCycleSystem` (`src/systems/strategic_systems/belief.py`) — a different, already-wired mechanism
`StrategicIntelligenceSystem.fused_strategic_pass` → `src/systems/strategic_systems/intelligence.py:405-438`
already runs its **own** inline contradiction check every tick, for `lead.kind == "location"` leads only, based
on proximity + hostile-neighbor perception (not resource depletion), calling
`BeliefCycleSystem.process_observation` / `BeliefCycleSystem.apply_contradiction`
(`belief.py:81-146`, `:148-183`). This is a **separate, already-production-wired** belief/contradiction path
that predates and does not overlap with `BeliefContradictionService`/`LeadContradictionSystem`. Do not confuse
the two when implementing — `BeliefCycleSystem` degrades certainty by one tier per contradiction
(PRECISE→APPROXIMATE→VAGUE→EXHAUSTED) via hostile-sighting proximity checks; `LeadContradictionSystem` jumps
straight to EXHAUSTED via resource/entity-existence checks. This ticket touches neither `BeliefCycleSystem` nor
`intelligence.py`.

### 6. `StrategicUpdate` / typed-update shape (`src/core/updates.py:474-534`)
`StrategicUpdate.leads_add_or_update: list[LeadState]` is the correct typed bucket
(`updates.py:480`). `EntityUpdate.strategic: Optional[StrategicUpdate]` (`updates.py:636`) and
`EntityUpdate.self_model_bundle_set: Optional[Any]` (`updates.py:649`) are the fields both
`LeadContradictionSystem.enforce()` and the new `BeliefContradictionService.detect()` call site must populate.
`EntityUpdate` has no generic `.merge()` shown in the excerpt read, but `LeadContradictionSystem.enforce()`
already demonstrates the safe merge pattern via `existing_ent_upd.strategic.merge(strat_upd)` — reuse this
exact pattern for the new call site rather than inventing a new one.

## Mechanics / Engine Constraints

- `docs/engine/authoritative_pipeline.md` — "The Singular Bottleneck Law": all state transitions must pass
  through `refine()`'s 38 phases; no system may mutate `AuthoritativeState` directly. Both new call sites
  (`lead_contradiction` phase, `BeliefContradictionService.detect()` call site) comply as designed — both
  return typed updates only.
- `docs/mechanics/04_strategic_cognition.md` §3 "Leads (Knowledge)" (line 89-93) states leads have a
  "Certainty: High, Medium, or Low. Certainty decays over time if the information is not refreshed" and §5
  (line 246) documents `BeliefCycleSystem.decay_stale_beliefs`'s 50-tick staleness decay — but nowhere
  documents that a lead can be *actively tested against world state* and marked EXHAUSTED with a provider
  reliability penalty. This is a genuine documentation gap for behavior the parity ledger (STRAT-230) already
  calls `verified` — see Docs Requiring Update.
- `docs/simulation/domains/information_contract.md` — "Lead Kind Classification (E42E)" (line 85-96) already
  documents all 5 `LeadKind` values and their *routing* behavior (via `LeadRoutingSystem`), and explicitly
  says (line 101) "If the entity is dead or absent → `belief_contradiction` event (handled by
  `LeadContradictionSystem`)" for PERSON leads — this line is currently **aspirationally true** (the logic
  exists and is correct) but **operationally false** (the system is never invoked in production). This is the
  authoritative domain contract for the exact behavior this ticket wires — must be checked for accuracy once
  OBJECT/EVENT/CONCEPT contradiction logic is added (their behavior is currently undocumented since it doesn't
  exist).

## Docs Requiring Update

- `docs/engine/authoritative_pipeline.md`: adding a `run_phase("lead_contradiction", ...)` call to
  `refine()` changes the enumerated phase count from 38 to 39; the "## The 38 Phases of Refinement" header,
  the summary table (currently phase-for-phase in sync with `pipeline.py`, confirmed by direct comparison),
  and the per-phase detail sections below it must all be updated to add the new phase in its inserted
  position and renumber subsequent phases.
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-230's `v2_evidence` currently cites
  `src/engine/pipeline_phases/lead_contradiction.py — LeadContradictionSystem.enforce()` as if it were live
  production evidence, with `test_path` pointing only at the isolated `.enforce()` unit test — this must be
  updated per the ticket's own AC4 to add the new full-pipeline-level test path once it exists (see Parity
  Ledger Overlap below for the exact current text).
- `docs/mechanics/04_strategic_cognition.md`: §3 "Leads (Knowledge)" (line 86-105) documents lead certainty
  decay but never documents contradiction-testing (EXHAUSTED via world-state mismatch, provider reliability
  penalty, UnknownFact regeneration for replanning) at all — this is the authoritative mechanics chapter for
  leads and is silent on a piece of lead lifecycle that, after this ticket, becomes live simulation behavior
  for the first time. A short new subsection (or addition to §3/§5) citing `LeadContradictionSystem` and the
  new OBJECT/EVENT/CONCEPT coverage is required.
- `docs/simulation/domains/information_contract.md`: the "PERSON Lead Routing" note (line 98-102) already
  claims `LeadContradictionSystem` handles the dead/absent case — once this ticket makes that operationally
  true, and once OBJECT/EVENT/CONCEPT contradiction coverage is added, the "Lead Kind Classification" table
  and its per-kind subsections should note which kinds now have contradiction coverage vs. which are routing-
  only, so the contract stays accurate about the newly-extended behavior (not just the pre-existing PERSON
  claim, which this ticket does not need to touch beyond making it true).

The `docs/simulation/domains/information_contract.md` "Authoritative Pipeline Integration" section (line
79-81, claiming `router.py` "dispatches to assimilation, contradiction, and trust update services") is a
**separate, pre-existing inaccuracy** not introduced by this ticket — `src/domains/information/router.py`
(`InformationQueryRouter.route()`) only scores/ranks candidate information sources for a query; it has no
dispatch logic to assimilation/contradiction/trust services at all. Per this ticket's explicit Out of Scope
("Correcting other docs beyond STRAT-230 that may have wrongly claimed `LeadContradictionSystem` was already
wired, beyond flagging the discrepancy found in this investigation"), this mismatch is flagged here but is not
this ticket's to fix.

The `docs/simulation/belief_and_detour_contract.md` doc (path: `docs/simulation/belief_and_detour_contract.md`)
is not required to change for this ticket: it documents `BeliefCycleSystem`'s certainty-demotion contradiction
mechanism (§"contradictions" field, `apply_contradiction`), which is the separate, already-wired adjacent
system described in Current Behavior §5 above — this ticket does not touch `BeliefCycleSystem` or that file's
subject matter.

## Parity Ledger Overlap

- **STRAT-230** (`docs/parity_ledger/strategic_cognition.yaml:2625-2646`), `status: verified`, `priority: P1`.
  Text: "When an entity's lead destination is inconsistent with world state ... the lead is marked
  FAILURE/EXHAUSTED, the originating provider's reliability_score is decremented by 0.1 (floored at 0.1) ...
  an UnknownFact (priority=0.7) is regenerated for replanning, a belief_contradiction SimulationEvent is
  emitted, and a lead_contradiction_resolved SimulationEvent is emitted." `v2_evidence` cites
  `LeadContradictionSystem.enforce()` directly, with no mention that it is unwired. `test_path` is
  `tests/unit/cognition/test_information_seeking.py::TestLeadContradiction::test_belief_contradiction_fires_on_depleted_lead;
  tests/unit/cognition/test_information_seeking.py::TestLeadContradiction` — **both** paths only exercise
  `LeadContradictionSystem.enforce()` called directly, never through `pipeline.refine()`. **This entry does
  not currently claim the system is wired into the pipeline in its `text`, but its `status: verified` combined
  with a test_path that never calls `refine()` reads as though full-pipeline behavior is proven when it is
  not** — this is the "wrongly claimed already wired" discrepancy the ticket references (worth being precise:
  the ledger doesn't literally say "wired into refine()", but its verified status implies more end-to-end
  coverage than exists; AC4 requires this be corrected with real pipeline-level evidence). This is a **P1**
  entry, not P0, so a passing `test_path` is required by convention/AC4 but not by the hard P0 gate rule.
- No other `strategic_cognition.yaml` entries (STRAT-001 through STRAT-097+ scanned; file is 3800+ lines)
  reference `lead_contradiction.py`, `contradiction.py`, or `BeliefContradictionService` by name in the portion
  reviewed. A full-file scan for `BeliefContradictionService`/`contradiction.py` beyond STRAT-230 was not
  completed given file size (3811 lines) — if the implementer finds another entry referencing these files, it
  should be updated alongside STRAT-230.
- No `docs/parity_ledger/*.yaml` entry currently documents `BeliefContradictionService.detect()`'s orphaned
  status or the OBJECT/EVENT/CONCEPT gap in `_is_lead_contradicted()` — STRAT-230's `text` is written entirely
  in terms of the resource/person-destination case; if the implementer extends `_is_lead_contradicted()` for
  OBJECT/EVENT/CONCEPT, either STRAT-230's `text` should be broadened or a new entry added — decide at
  planning time based on whether the new coverage is a natural extension of the same law or a distinct one.

## Prior Work

- **TCK-20260619-E42D-CONTRADICTION** (`tickets/done/`, `stored_artifacts/TCK-20260619-E42D-CONTRADICTION/`):
  original ticket that built `LeadContradictionSystem` and `BeliefContradictionService`. Its own "Assumptions /
  Open Questions" section already flagged: "SimulationEvents are not part of StateUpdate... the belief_
  contradiction 'event' is signalled via metric_counters in the StateUpdate so the kernel can observe it, and
  the actual SimulationEvent emission is done by the new pipeline phase when called in a kernel context" —
  i.e. the original ticket already anticipated that "when called in a kernel context" was a future step, not
  something it itself delivered. This matches the finding that the phase was built but never wired.
- **TCK-20260619-E42-INFO-SEEKING** (epic, `tickets/done/`): parent epic; scope explicitly lists "Lead
  contradiction: belief_contradiction event; provider reliability_score decrements" and "PERSON_LEAD and
  CONCEPT_LEAD via LeadKind enum migration" as two of its child deliverables — confirming CONCEPT/PERSON lead
  support (routing) and contradiction detection were scoped as siblings, not as one integrated path; this
  ticket is closing the gap between them.
- **TCK-20260619-E42E-LEAD-TYPES** (`tickets/done/`): built the `LeadKind` enum and `LeadRoutingSystem` — this
  is where OBJECT/EVENT/CONCEPT routing (but not contradiction-testing) originates.
  Its stored artifacts (not read in full for this investigation; recommend implementer skim
  `stored_artifacts/TCK-20260619-E42E-LEAD-TYPES/plan.md` if one exists, for the original design rationale
  behind leaving OBJECT/EVENT contradiction unhandled).
- **TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS** (working_log.csv / registry entry; actual stored artifacts filed
  under `stored_artifacts/TCK-20260701-SIMQ-EMIT-INFORMATION2/` — a ticket-id/folder-name mismatch worth
  noting but not fixing here): added the `lead_contradiction_resolved` event emitter (visible already in
  `lead_contradiction.py:237-250`) and added STRAT-240–242 parity entries for SimQ event coverage — confirms
  the event *shape* was already reviewed for SimQ scoring purposes, independent of production wiring.
- **`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`** (cited in `information_intent_execution.py`'s docstring):
  precedent for exactly this ticket's shape of problem — a decision phase (`InformationBeliefPhase` Branch B)
  produced a result that was stored but never executed, until a follow-up ticket added the missing production
  call site (`InformationIntentExecutionPhase`). Same "phase writes typed results, nothing consumes them
  in-tick" pattern as `BeliefContradictionService`/`ObservationBeliefBridge` today. Worth reading as a template
  for how a previous ticket in this codebase solved the identical class of gap.

## Risks and Open Questions

1. **Where do `claim_failed_search`/`region_danger_seen` observation events originate in production?**
   Confirmed: nowhere today. This ticket's AC2 requires `BeliefContradictionService.detect()` be invoked "when
   a claim_failed_search/region_danger_seen observation is processed" — but no system currently produces such
   an observation dict. The implementer must either (a) add a new observation-event producer (e.g. from a
   failed harvest/search action outcome or a perception-detected regional danger signal) as part of this
   ticket, or (b) add the consumer plumbing (a `pending_observation_events`-shaped input to
   `InformationBeliefPhase.apply()`, mirroring `pending_information_responses`) and defer producing real
   events to a follow-up ticket, verified only via direct unit tests that hand-construct observation dicts (as
   the existing `test_phase5_belief_contradiction.py` already does). **This should be resolved at planning
   time, not assumed** — the two interpretations materially change scope size.
2. **CONCEPT-lead contradiction: state-scan or observation-driven?** As detailed in Current Behavior §3,
   CONCEPT leads don't have an obvious `state.<registry>` to scan (unlike OBJECT's `ground_items`/`chests` or
   EVENT's `local_scars`/`recent_world_events`); their natural contradiction trigger is a failed
   `PaidInformationTransactionSystem` query, which is observation-shaped, not state-scan-shaped. Implementer
   must decide whether to (a) force CONCEPT into `_is_lead_contradicted()`'s state-scan shape anyway (with some
   proxy check), or (b) route CONCEPT contradiction through the `BeliefContradictionService.detect()` call
   site instead, leaving `_is_lead_contradicted()`'s CONCEPT branch permanently `return False` (matching the
   existing precedent set for `"information"` kind leads at line 90-94, which are also "not validated against
   world state here" by design). Flagging both as valid before implementation.
3. **EVENT-lead world-state check has no obvious existing helper.** No function in the reviewed code answers
   "is this world event/regional trauma still true" in a form `_is_lead_contradicted()` can call directly.
   `docs/mechanics/05_world_evolution.md` (regional trauma/calamity chapter) was not read in this investigation
   and should be checked before implementation for the right state surface (`state.local_scars`? a
   trauma-decay timestamp?).
4. **`ENABLE_LEAD_CONTRADICTION` feature flag and `PhaseDependencyGraph`**: `src/engine/phase_graph.py`
   (`PhaseDependencyGraph.should_run_phase`) was not read in this investigation. Every existing `run_phase()`
   call implicitly depends on this module returning `True`/appropriate cadence behavior for a new,
   previously-unregistered phase name; confirm it defaults sanely for unknown phase names (likely yes, given
   how many optionally-flagged phases already exist) before assuming no change is needed there.
5. **STRAT-230's own `text`** describes only the resource/person-destination case; if OBJECT/EVENT/CONCEPT
   coverage is added under the same `_is_lead_contradicted()` umbrella, decide whether STRAT-230's `text`
   should be broadened (single law, wider coverage) or a new STRAT-2xx entry added (separate law) — do not
   silently leave STRAT-230's `text` inconsistent with its own `v2_evidence` after implementation.

## Anti-Drift Hazards

- **Do not touch `BeliefCycleSystem`** (`src/systems/strategic_systems/belief.py`) or its production call site
  in `src/systems/strategic_systems/intelligence.py:405-438` — it is a separate, already-wired,
  already-correct contradiction mechanism for `location`-kind leads via hostile-proximity observation. It is
  easy to confuse with `BeliefContradictionService` because both concepts are named "contradiction" and both
  touch `LeadCertainty`; they are not the same system and this ticket's scope does not include it.
- **Do not conflate `LeadRoutingSystem`** (`src/engine/domain/lead_routing.py`, routing/navigation target
  resolution, already fully wired via `detour.py`) **with `_is_lead_contradicted()`** (world-state
  contradiction testing, the actual gap). Extending OBJECT/EVENT/CONCEPT means adding contradiction-testing
  branches, not touching routing — `LeadRoutingSystem` already works correctly for all 5 kinds and should not
  be modified.
- **Do not let the new `lead_contradiction` phase build a fresh `StateUpdate()` and return it wholesale** —
  the `CombatEngagementPhase` bug documented inline at `pipeline.py:266-276`
  (`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS`) is the exact failure mode to avoid:
  `LeadContradictionSystem.enforce()` already correctly takes `update` as an argument and merges into it
  (`entity_updates = dict(update.entity_updates)` at line 123), so as long as the new `run_phase()` lambda
  passes `u` straight into `.enforce(state, u)` (not `.enforce(state, StateUpdate())`), this is already safe —
  but verify this explicitly in the implementer's diff, since it's the single most common way this class of
  wiring ticket goes wrong in this codebase.
- **Do not mark `"resource"` as a real `LeadKind`** when extending `_is_lead_contradicted()` — it is dead code
  today and should likely be removed (or left as harmless dead code) rather than "fixed" into a working branch,
  since no production path ever produces `kind="resource"` and inventing new production callers for it is
  outside this ticket's stated scope (OBJECT/CONCEPT/EVENT only).
- **Do not widen `BeliefContradictionService.detect()`'s scope beyond `claim_failed_search`/
  `region_danger_seen`** while wiring its call site — AC2 is specific to those two observation kinds; the
  existing `detect()` implementation already only handles those two (`contradiction.py:50`, `:60`), so no
  change to `detect()` itself should be needed, only its caller.
