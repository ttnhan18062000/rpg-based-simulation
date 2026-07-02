# Investigation — TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO

**Ticket:** TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO  
**Date:** 2026-07-02  
**Investigator:** Agent (seq 2)  
**Status:** Complete

---

## Summary

FACTION, SOCIAL, and INFORMATION pillars show ZERO calibration_hits across all 25 calibration runs. Root cause is confirmed **hypothesis (c): the underlying engine mechanics never trigger in practice** — for each pillar, the EventExtractor emission code is correct and wired, but the upstream conditions that produce the state diffs it reads from are never satisfied in standard calibration worlds.

There are three independent (c) sub-causes, one per pillar:

| Pillar | Root Cause | Key Gate |
|---|---|---|
| FACTION | `faction_updates` always empty — no FactionState has non-zero tension or territory in any calibration world | World content: all factions start with `tension_level=0.0`, `territory=()` |
| SOCIAL | `ENABLE_SOCIAL_COOPERATION=OFF` by default — CooperationPhase never runs; `last_cooperation_decision` property never set; `trust_history` never written; contracts never created | Feature flag default |
| INFORMATION | `ENABLE_BELIEF_ASSIMILATION=OFF` by default — InformationBeliefPhase never runs; `last_assimilated_tick` never set; `leads` map never populated | Feature flag default |

---

## Current Behavior (with file:line refs)

### FACTION Pillar

**EventExtractor emission points** (`src/observability/event_extractor.py`):

- `diplomatic_transition` — L945–959: reads `update.faction_updates`, iterates `upd.diplomatic_relations_set`. Fires only when a `FactionUpdate` with non-empty `diplomatic_relations_set` is in the update.
- `faction_tension_delta` — L1001–1007: reads `upd.tension_delta != 0.0` from a `FactionUpdate`.
- `alliance_proposed` / `alliance_accepted` — L961–981: fires when `new_state == "ALLIED"` in a diplomatic_relations_set update.
- `territory_ownership_changed` / `resource_seized` — L984–998: reads `upd.territory_add`.
- `war_declared` / `military_conflict_resolved` — L1019–1035: reads `update.world_events_add` for `FACTION_WAR_DECLARED` / `TERRITORY_TRANSFERRED` / `WAR_ENDED_EXHAUSTION`.
- `faction_extinct` — L1085–1113: fires only when `faction_updates` list is non-empty AND a faction has no living members.

**Pipeline faction update sources** (`src/engine/pipeline.py`):

1. **Phase 8c — FactionAwareness** (L174–183): `FactionAwarenessService.compute_tension_updates()` — returns `FactionUpdate(tension_delta=0.1)` only for factions whose territory contains a region with a recent `RESOURCE_DEPLETED` WorldEvent. Requires: faction has territory AND resource node in that territory was depleted recently.

2. **Phase 8d — DiplomaticStateMachine** (L186–213): `compute_transitions()` — fires NEUTRAL→TENSE when `pair_tension > 0.4`, TENSE→HOSTILE when `pair_tension > 0.7` or shared territory, HOSTILE→WAR, WAR→NEUTRAL. `pair_tension = max(fa.tension_level, fb.tension_level)`. Alliance generation via `compute_common_enemy_pairs()` — requires at least two factions both HOSTILE toward a third.

3. **Phase 8e — MilitaryConflict** (L216–223): fires territory transfer and military_strength changes.

**Actual faction state in calibration worlds:**

`FactionState.tension_level` defaults to `0.0` (src/core/state.py L615). `FactionState.territory` defaults to `()` (L610). The world compile reports show `factions=?` (faction_count not exposed in compile report) but the world YAML files for `dungeon_crawl` and `urban_political` have no `^factions:` block at the YAML root — factions are content catalog entries only (`src/content_semantics/faction.py`), not `FactionState` objects in `AuthoritativeState`. Consequently:

- `state.factions` is likely an empty dict in all calibration worlds, or factions exist but with `tension_level=0.0` and `territory=()`.
- `compute_transitions()` requires `pair_tension > 0.4` to fire — impossible when all `tension_level=0.0`.
- `FactionAwarenessService` requires factions to have territory — impossible when `territory=()`.
- `MilitaryConflictPhase` requires WAR state — impossible to reach from NEUTRAL with zero tension.
- All `faction_updates` lists remain empty every tick. EventExtractor faction loop never fires.

### SOCIAL Pillar

**EventExtractor emission points** (`src/observability/event_extractor.py`):

- `cooperation_event` — L302–309: reads `prop.get("last_cooperation_decision")` from `EntityUpdate.property_updates`. Set only by CooperationPhase (L134–136 of `src/domains/cooperation/phase.py`).
- `social_memory_created` — L524–546: reads `entity.social.trust_history` diff. `trust_history` is `Dict[int, float]` in `SocialComponent` (L25 of `src/core/models/social.py`), updated via `SocialUpdate.trust_delta` in apply.py. CooperationPhase writes `trust_delta` only in the party-cohesion-collapse path (L150–154), and only when `g_rec.status in ("MEMBER_ABANDONING", "LEADER_LOST")`.
- `group_joined` / `group_expelled` — L489–505: reads `entity.group_id` vs `prior_ent.group_id`. Groups only form via CooperationPhase.
- `reputation_delta` — L508–521: reads `entity.social.public_reputation` diff. `public_reputation` starts at `1.0` and is never written in any pipeline phase during normal entity-loop operation.
- Contract events (`contract_offer_created`, `contract_offer_accepted`, etc.) — L549–644: reads `entity.strategic.contracts` diff. Contracts are created by `CooperationIntentBridge.map_decision()` in CooperationPhase — which never runs.

**Root cause:** `ENABLE_SOCIAL_COOPERATION` defaults to `FeatureMode.OFF` (`src/domains/optimization/feature_flags.py` L20). `run_phase("cooperation", ...)` returns the input update unchanged. `last_cooperation_decision` is never set in any EntityUpdate.property_updates. `trust_history` is never written (only path is CooperationPhase cohesion collapse). `contracts` on `entity.strategic` are never created. Every SOCIAL emitter condition is permanently unsatisfied.

### INFORMATION Pillar

**EventExtractor emission points** (`src/observability/event_extractor.py`):

- `belief_assimilated` — L286–299: reads `prop.get("last_assimilated_tick") == tick`. Set only by `InformationBeliefPhase.apply()` (L76 of `src/domains/information/phase.py`) when a pending_response is assimilated.
- `lead_certainty_updated` — L415–428: reads `entity.strategic.leads` map, comparing `lead.certainty` to `prior_lead.certainty`. Fires when certainty enum changes. Leads are populated by InformationBeliefPhase / StrategicIntelligenceSystem.
- `belief_stale` — L430–446: reads lead certainty and `discovered_tick`. Requires leads in strategic component.
- `decision_diverged_by_belief` — L451–465: requires `entity.strategic.leads` with VAGUE/EXHAUSTED certainty AND a current project.
- `paid_information_transaction` — L358–365: requires `src_kind == "INFORMATION_PURCHASE"` in intent_results, which requires an `InformationIntentResolver.resolve()` call from InformationBeliefPhase.
- `lead_certainty_updated` via `lead_contradiction_resolved` — emitted from `src/engine/pipeline_phases/lead_contradiction.py` (confirmed in §3.3 of event_type_coverage.md) — requires leads with contradicting certainty.

**Root cause:** `ENABLE_BELIEF_ASSIMILATION` defaults to `FeatureMode.OFF` (`src/domains/optimization/feature_flags.py` L18). `run_phase("information_belief", ...)` never executes `InformationBeliefPhase.apply()`. `last_assimilated_tick` is never set. Furthermore `state.pending_information_responses` is likely always `[]` and `state.information_source_profiles` always `[]` even if the flag were enabled — InformationBeliefPhase has no responses to process. The `leads` map on `entity.strategic` is never populated from the belief pipeline, so all lead-based emitters (belief_stale, lead_certainty_updated, decision_diverged_by_belief) are also moot.

---

## Root Cause Analysis

**Classification: (c) — Engine mechanics never trigger.**

All three pillars are classified (c). The evidence for ruling out (a) and (b):

**Against (a) — EventExtractor not emitting:**
- FACTION: All faction event emitters are present and correct in event_extractor.py L937–1113. They gate on `update.faction_updates` being non-empty. The list is always empty because no pipeline phase ever produces a non-noop FactionUpdate in calibration worlds. The EventExtractor code is not at fault.
- SOCIAL: `cooperation_event` and `social_memory_created` emitters are present (L302–309, L524–546). They gate on state/property diffs that are never produced. The code is correct.
- INFORMATION: `belief_assimilated` emitter is present (L286–299). It gates on `prop.get("last_assimilated_tick") == tick`. This is never true.

**Against (b) — weights=0:**
- Weights were not inspected directly but can be ruled out: zero calibration_hits means the scorers receive zero envelopes with matching event_type. A weight=0 bug would produce a ScoreRecord with delta=0, which would still increment event_count. The evidence is `event_count=0`, not `raw_score=0 with event_count>0`.

**For (c) — mechanics never trigger, per pillar:**

**FACTION (c1 — world content gap):**
The DiplomaticStateMachine `compute_transitions()` requires `pair_tension > 0.4` to fire NEUTRAL→TENSE. All factions start at `tension_level=0.0` (FactionState default). `FactionAwarenessService` requires factions with non-empty territory (`if event.region_id in fs.territory`) to produce tension deltas. No calibration world assigns territory to factions at compile time. The result is that `tension_level` remains 0.0 for every faction throughout every run, `faction_updates` is always empty, and the entire diplomatic pipeline produces no observable state changes. This is confirmed by the P1-C audit finding ("Faction interaction logic absent... engine has no system that uses faction stance to drive entity-level behavioural differences") and by the KS search result ("Zero engine code exists" for faction diplomacy as of pre-E53, and the E53 epic only added the engine mechanics — not the world content that seeds initial tension or territory).

**SOCIAL (c2 — feature flag OFF):**
`ENABLE_SOCIAL_COOPERATION = FeatureMode.OFF` in `src/domains/optimization/feature_flags.py` L20. CooperationPhase is skipped every tick. No entity ever gets `last_cooperation_decision` in property_updates. No trust_history is ever written. No contracts are ever created. This is the same flag-default pattern as AGENCY (`ENABLE_ADVENTURE_ROUTING=OFF`) documented in P0-A.

**INFORMATION (c3 — feature flag OFF + no data pathway):**
`ENABLE_BELIEF_ASSIMILATION = FeatureMode.OFF` in `src/domains/optimization/feature_flags.py` L18. InformationBeliefPhase never runs. Even if it ran, `state.pending_information_responses` is populated only by the information sub-system response cycle, which itself requires either the adventure routing pipeline (OFF) or explicit pending_responses injection. The leads map is never populated from the standard pipeline. INFORMATION scoring has a dual gate: flag OFF AND no data pathway to produce responses.

---

## Mechanics / Engine Constraints

### FACTION — what is needed to activate

1. **Initial tension or territory in world spec:** At least one faction pair needs `tension_level >= 0.4` at world compile, OR at least one faction needs non-empty `territory` (region_ids). Without this, no path exists to the first `NEUTRAL→TENSE` transition.
2. **Resource depletion in faction territory:** For `FactionAwarenessService` to fire tension deltas via resource depletion events, a faction must own territory containing a resource node that gets depleted in play.
3. **Military strength asymmetry:** For HOSTILE→WAR, one faction must have `military_strength > other * 1.2`. Default is `military_strength=1.0` for all factions — symmetric, so no WAR transition is possible.

**Minimum viable activation (world content change):** Set `tension_level=0.5` on at least two factions with a defined diplomatic relationship, OR assign `territory` of at least one region to each of two factions. This immediately enables `compute_transitions()` to fire NEUTRAL→TENSE→HOSTILE within a few ticks.

### SOCIAL — what is needed to activate

Enable `ENABLE_SOCIAL_COOPERATION` in the calibration run profile (rollout_profile or feature_flags on state). CooperationPhase requires: entities alive (`entity.lifecycle.active and entity.combat.alive`), help needs detected by `HelpNeedEvaluator`, or existing group membership. When the flag is ON, the phase runs every tick with `budget = CandidateBudget(max_candidates=5, spatial_radius=15.0)`. Contract creation flows from `CooperationIntentBridge.map_decision()`. Trust writes flow from the party-cohesion collapse path and potentially from `CooperationLearningService`. With the flag ON and multiple active entities, `cooperation_event`, `group_joined`, `social_memory_created`, `contract_*` events should all fire within 50–100 ticks.

**Note:** `SocialScorer._cooperation_dormant_fired` is triggered by the `cooperation_event` event_type check at L58–71 of social.py, not by an independent timer. The dormancy penalty only fires when a `cooperation_event` envelope arrives AND tick > stagnation_window AND event_count == 0. Since no envelopes ever arrive, this path also never fires.

### INFORMATION — what is needed to activate

Enable `ENABLE_BELIEF_ASSIMILATION` AND provide both `state.information_source_profiles` (non-empty list of `InformationSourceProfile` objects) AND either (a) seed `state.pending_information_responses` with responses, or (b) enable a pathway that populates `entity.self_model.knowledge.unknowns` so the phase routes new queries. Without information_source_profiles, `InformationQueryRouter.route()` returns no candidates and no intent is produced. Additionally, the adventure routing pipeline (ENABLE_ADVENTURE_ROUTING) must be ON for entities to generate information-seeking projects that ultimately produce paid_information_transaction events.

---

## Parity Ledger Overlap

From `docs/parity_ledger/social_narrative.yaml`:

| Parity ID | Description | Status | Relevant to this ticket |
|---|---|---|---|
| SOC-236 | EventExtractor emits faction tension/alliance/war events from faction_updates | verified | Yes — emission confirmed wired; upstream not triggered |
| SOC-237 | social_memory_created emitted from EventExtractor on trust_history delta | verified | Yes — emitter wired; trust_history never written (SOCIAL phase OFF) |
| SOC-238 | contract_milestone_completed time-gated emitter | verified | Yes — emitter wired; contracts never created |

From `docs/parity_ledger/faction.yaml`:

| Parity ID | Description | Status | Relevant to this ticket |
|---|---|---|---|
| FACTION-TENSION-001 | FactionAwarenessService produces tension delta from RESOURCE_DEPLETED events in faction territory | verified | Yes — code verified; upstream condition never met (no territory) |
| FAC-006 | DiplomaticStateMachine compute_transitions applied via pipeline Phase 8d | verified | Yes — wiring verified; transitions never fire (tension_level=0.0) |

None of the above parity entries need status changes — they document the mechanics accurately. The gap is world content and feature flags, not a parity divergence. No new parity entries are required unless a behavior change is implemented.

---

## Prior Work

### TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION
**Claimed:** "6 social + 7 faction events emitted; 3 contract bug fixes; 53 new tests."
**What it actually did:** Added all EventExtractor emission blocks for SOCIAL and FACTION events (cooperation_event, contract_*, group_joined/expelled, reputation_delta, diplomatic_transition, alliance_accepted, war_declared, military_conflict_resolved, territory_ownership_changed, faction_tension_delta, faction_extinct). Added translation entries `leadership_changed→diplomatic_transition`, `alliance_formed→alliance_accepted`, `betrayal_desertion→conditional`. The emission code is correct and unit-tested.
**What it did NOT do:** Did not verify that the upstream conditions (CooperationPhase enabled, factions with tension/territory) ever fire in calibration runs. Tests were unit tests with synthetic inputs — they proved the emitter code is correct, not that the engine produces the inputs.

### TCK-20260701-SIMQ-EMIT-SOCIAL2 (TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY)
**Claimed:** "Remaining SOCIAL/FACTION/INFORMATION stubs closed."
**What it actually did:** Added `alliance_proposed`, `resource_seized` emitters to EventExtractor. Added `social_memory_created` (TCK-20260701-SIMQ-EMIT-SOCIAL-MEM separately) and `contract_milestone_completed` (TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE separately). Declared `engine_emission_gaps = 0`. This was correct: all emission infrastructure exists. The declaration of "gaps resolved" was valid for the emission layer but did not evaluate the activation layer.

### TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS
**Claimed:** "6 emitters added (lead_certainty_updated, belief_stale, paid_info_changed_goal, decision_diverged_by_belief, decision_divergence_detected, lead_contradiction_resolved)."
**What it actually did:** Added all INFORMATION emitters to EventExtractor (L396–465 of event_extractor.py). All emitters read from `entity.strategic.leads` and `EntityUpdate.property_updates["last_assimilated_tick"]`. Gating condition `prop.get("last_assimilated_tick") == tick` requires InformationBeliefPhase to run — which requires ENABLE_BELIEF_ASSIMILATION=ON. Tests were synthetic (unit tests with pre-populated leads). Calibration baseline was not re-run to confirm non-zero hits.

**Pattern across all prior work:** Each ticket added correct emission infrastructure and declared the gap closed based on unit tests. None verified end-to-end activation in a real calibration run. The calibration corpus (`data/calibration/*/quality_scores.jsonl`) shows zero hits for all three pillars, which is the definitive ground truth.

---

## Risks and Open Questions

**R1 — Feature flags ON may break other things:**
CooperationPhase and InformationBeliefPhase are both listed as `FeatureMode.OFF` alongside `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_ADVENTURE_ROUTING`, and `ENABLE_COMBAT_ENGAGEMENT`. These were likely set OFF because they are not yet stable or because they depend on other flags being ON first. Enabling SOCIAL cooperation independently of ADVENTURE_ROUTING may produce unexpected interactions (e.g., cooperation decisions set as property_updates but adventure_decision phase not consuming faction_directives for social routing). Risk: medium. Mitigation: enable in isolation on a targeted calibration run before enabling in all calibration profiles.

**R2 — InformationBeliefPhase requires data that is never seeded:**
Even with ENABLE_BELIEF_ASSIMILATION=ON, InformationBeliefPhase.apply() requires `state.pending_information_responses` and `state.information_source_profiles` to be populated. In all current calibration worlds, these are empty lists (set via `getattr(state, "information_source_profiles", [])`). The phase will run but produce empty entity_updates. This means enabling the flag alone is insufficient — the world or scenario must also seed information sources. This is a deeper activation gap than a flag toggle.

**R3 — FACTION activation via world content change may require world recompilation:**
If FactionState with non-zero tension_level and territory is added to world specs, this requires the WorldAssemblyResolver and WorldCompiler to be re-run for each affected world. This is a content authoring task, not a code change. It may interact with the existing P0-C bug (entity navigation.region_id = None) if territory-based routing is involved.

**R4 — Dormant penalty paths may fire incorrectly after fix:**
Both FactionScorer (`_diplomacy_dormant_fired`) and SocialScorer (`_cooperation_dormant_fired`) have zero-event penalty paths that fire when the first event of the relevant type arrives AND event_count was previously 0 AND tick > gate. After fixing the upstream activation, the first event arrival will trigger the dormancy check. If the gate tick (e.g., `stagnation_window`) is already exceeded at the time of first event, the dormancy penalty fires instead of the positive score. This would produce a negative quality signal on first activation. Verify the gate ticks relative to typical first-event tick in calibration runs.

**R5 — Prior audit base (200t) may not expose these failures:**
The event_type_coverage.md audit base was 200t runs. Even with activation changes, some events (faction_extinct, war_declared) require sustained conflict over many ticks. 200t calibration runs may not produce them. Recommended verification tick count: 500t minimum for FACTION events, 200t sufficient for SOCIAL (cooperation decisions should fire within 10 ticks once CooperationPhase is ON).

**AQ1 — Do any calibration worlds actually compile factions into AuthoritativeState.factions?**
The compile reports show `factions=?` (field not exposed). World YAML files for dungeon_crawl and urban_political have faction references in entity archetypes but no root-level factions block. If `state.factions` is an empty dict in all calibration worlds, then Phase 8d runs `compute_transitions({})` which returns []. This would make FACTION fixable only via world content authoring, not a code change.

**AQ2 — Is SocialUpdate.trust_delta applied to entity.social.trust_history in apply.py?**
`apply.py` L565 shows `"social": changes.get("social", entity.social)` — social component is replaced wholesale. `SocialUpdate.trust_delta` must be merged into the component in apply.py. This path was not fully traced; verify that `apply.py` correctly accumulates `trust_delta` into `entity.social.trust_history` before relying on social_memory_created to fire.

---

## FACTION Deferral

Root cause c1 confirmed: `WorldCompiler.compile()` does NOT construct `FactionState` objects. Confirmed by grep: no `FactionState(` constructor call exists in `compiler.py`. The compiler processes `spec.factions` at line 177 but only initializes vault gold — `state.factions` is populated only via `faction_updates` in `apply.py`'s `apply_generation`, which requires an existing `FactionState` or creates a zero-tension default.

Seeding `tension_level` in the world YAML has zero effect without a compiler code path that reads and applies it. Consequence: all factions start at `tension_level=0.0` every run, `compute_transitions()` never fires NEUTRAL→TENSE (requires `pair_tension > 0.4`), and `faction_updates` remains empty every tick.

**Follow-up ticket required with scope:**
1. Extend `WorldSpec` schema with a `FactionStateSpec` model (tension_level, diplomatic_relations, military_strength fields).
2. Extend `WorldCompiler.compile()` to construct `FactionState` objects from `FactionStateSpec` and populate `state.factions`.
3. Seed `urban_political` world with `bandit_company`/`town_council` at `tension_level=0.5`, `diplomatic_relations: {<other>: NEUTRAL}`.
4. Verify `diplomatic_transition` event fires in calibration run.
5. Do NOT add territory (avoids P0-C `region_id=None` navigation interaction).

## INFORMATION Deferral

Root cause c3 confirmed: dual gate — (1) `ENABLE_BELIEF_ASSIMILATION=OFF` by default AND (2) `state.information_source_profiles=[]` and `state.pending_information_responses=[]` in all calibration worlds.

Enabling the flag alone is insufficient. `InformationBeliefPhase.apply()` calls `InformationQueryRouter.route()` which returns no candidates when `information_source_profiles` is empty. No intent is produced, `last_assimilated_tick` is never set, `belief_assimilated` never fires.

The data gate requires either:
- Adding `InformationSourceProfile` objects to world specs (new schema/compiler work), OR
- Seeding `state.pending_information_responses` in the calibration runner (synthetic injection, less authentic).

This is a dual-gate problem distinct from the SOCIAL single-gate fix. Not addressed in this ticket per plan scope.

**Expected post-fix state:** INFORMATION pillar remains at `event_count=0`, `grade=C` in all calibration runs. Documented and intentional — not a regression.

**Follow-up ticket suggested scope:** (1) Add `information_source_profiles` field to at least one world spec; (2) enable `ENABLE_BELIEF_ASSIMILATION` in that world's calibration profile YAML `feature_flags:` block; (3) verify `belief_assimilated` fires in calibration run; (4) update grade_anchors and event_type_coverage.md.

## Anti-Drift Hazards

1. **Emission code declared done but calibration_hits=0:** The pattern of claiming emission gaps closed without running calibration must not repeat. Any new emitter addition must be followed by a calibration run verification step before the ticket is declared DONE.

2. **Feature flags as silent suppressors:** ENABLE_SOCIAL_COOPERATION and ENABLE_BELIEF_ASSIMILATION are silent OFF switches that make entire pillars invisible. Their state must be explicitly documented in the calibration run profile used for each quality score run. The calibration corpus metadata should record which flags were enabled.

3. **World content as silent suppressor for FACTION:** Even with all code correct, FACTION scoring requires world content (faction tension, territory). Adding an emitter without seeding this content produces zero calibration_hits. Future faction-related tickets must specify the calibration world configuration as part of the test plan.

4. **ScoringContext.pillar_event_counts is a live counter:** The dormant-fire paths in FactionScorer and SocialScorer read `context.pillar_event_counts.get(PillarId.FACTION, 0) == 0`. This check is valid only before the first event is processed. Once the pillar is activated and first event fires, the dormant path is permanently suppressed. If activation is partial (events fire infrequently), the dormant penalty will never fire either — producing no signal rather than the intended penalty. This is a measurement blind spot.
