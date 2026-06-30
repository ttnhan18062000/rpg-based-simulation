# SimQ Event Type Coverage

**Status:** Certified Level 1 — Authoritative  
**Ticket:** TCK-20260630-SIMQ-TRANSLATE  
**Date:** 2026-06-30  
**Audit base:** calibration runs in `data/calibration/` (sandbox_world seeds 42/137/999 200t, dungeon_crawl 200t, urban_political 200t, wilderness_survival 200t, simq_routing_test 500t)

---

## Summary

| Category | Count |
|---|---|
| scored | 55 |
| translation_gap | 0 |
| engine_emission_gap | 27 |
| p0_a_blocked | 3 |
| unscored_intentional | 13 |

**Translation table status:** Complete. All 8 `_TRANSLATE_SIMPLE` and 5 `_TRANSLATE_CONDITIONAL` entries in `quality_hub.py` are correct. No translation table gaps found.

**Gaps found:** 27 entries in SCORER_REGISTRY that will never be reached because the engine does not yet emit the corresponding event types. These are infrastructure stubs — scoring logic exists but upstream emission is deferred. See §3 (Engine Emission Gaps).

---

## Classification Definitions

| Classification | Meaning |
|---|---|
| `scored` | Event is emitted by the engine AND reaches the correct scorer(s) via direct match or translation |
| `translation_gap` | Event is emitted but the translation table has a missing or wrong mapping so it never reaches the scorer |
| `engine_emission_gap` | SCORER_REGISTRY entry exists (scorer ready) but the engine does not emit this event type yet |
| `p0_a_blocked` | Scorer entry exists but the event is gated by a feature flag (ENABLE_ADVENTURE_ROUTING) or infrastructure (campaigns/scenario system) that is OFF in all calibration runs |
| `unscored_intentional` | Event is emitted by the engine but is not wired to any scorer — deliberate |

---

## §1 Scored Events

All events below are emitted by the engine and reach at least one pillar scorer, either directly (contract vocabulary already matches) or after `QualityHub._translate()` remaps the engine event_type.

### §1.1 Direct Emission — No Translation Required

| event_type | source | scorers | calibration_hits | notes |
|---|---|---|---|---|
| `demographic_mortality` | event_extractor | WorldDynamicsScorer | 0 | Emitted only on despawn-without-attacker; rare in short runs |
| `demographic_birth` | event_extractor | WorldDynamicsScorer | 0 | Emitted on entity spawn; scored via world_dynamics pillar |
| `hero_death_unrecorded` | event_extractor | NarrativeScorer | 0 | Only for kind="hero" entities |
| `combat_damage` | CombatDamageEvent | CombatScorer | 0 | Light/long-run mode suppresses non-lethal; lethal path hits scorer |
| `combat_initiated` | event_extractor | CombatScorer | 117 | Fires when entity at full HP takes first hit |
| `near_death_survival` | event_extractor | CombatScorer, ProgressionScorer | 164 | HP crosses below 20% threshold |
| `xp_granted` | event_extractor | ProgressionScorer | 0 | Fires on identity.evolution_points delta |
| `level_up` | event_extractor | ProgressionScorer | 0 | Direct path; also reachable via `lifecycle` translation |
| `route_selected` | event_extractor | AgencyScorer | 20 | Fires when entity.last_routing_family changes |
| `action_executed` | event_extractor | AgencyScorer | 20 | Co-fires with route_selected |
| `self_model_updated` | event_extractor | CognitionScorer | 0 | Fires on self_model_bundle_set |
| `belief_assimilated` | event_extractor | InformationScorer | 0 | Fires on last_assimilated_tick == current_tick |
| `belief_updated` | event_extractor | CognitionScorer | 0 | Co-fires with belief_assimilated |
| `cooperation_event` | event_extractor | SocialScorer | 0 | Fires on last_cooperation_decision |
| `resource_harvested` | event_extractor | EconomyScorer | 0 | src_kind=NODE in intent_results |
| `item_crafted` | event_extractor | EconomyScorer | 0 | src_kind=CRAFTING |
| `shop_transaction` | event_extractor | EconomyScorer | 0 | src_kind=SHOP_BUY or SHOP_SELL |
| `trade_executed` | event_extractor | EconomyScorer | 0 | Co-fires with shop_transaction |
| `quest_reward_dispensed` | event_extractor | EconomyScorer | 0 | src_kind=QUEST |
| `gold_sink_fired` | event_extractor | EconomyScorer | 0 | src_kind in (REPAIR_FEE, SERVICE_FEE, TAX) |
| `paid_information_transaction` | event_extractor | InformationScorer | 0 | src_kind=INFORMATION_PURCHASE; see §3 note on `paid_info_transaction` |
| `hazard_drain_applied` | event_extractor | WorldDynamicsScorer | 322 | combat_upd.outcome_kind=="HAZARD" |
| `lead_certainty_changed` | event_extractor | CognitionScorer | 0 | Strategic lead certainty state diff; see §3 note on `lead_certainty_updated` |
| `group_joined` | event_extractor | SocialScorer | 0 | Entity joins a group |
| `group_expelled` | event_extractor | SocialScorer | 0 | Entity leaves a group |
| `reputation_delta` | event_extractor | SocialScorer | 0 | public_reputation delta > 0.05 |
| `contract_offer_created` | event_extractor | SocialScorer | 0 | New contract in OFFERED state |
| `contract_offer_accepted` | event_extractor | SocialScorer | 0 | OFFERED → ACTIVE transition |
| `contract_completed` | event_extractor | SocialScorer | 0 | Contract reaches FULFILLED |
| `contract_lapsed` | event_extractor | SocialScorer | 0 | ACTIVE → EXPIRED |
| `contract_expired_offer` | event_extractor | SocialScorer | 0 | OFFERED → EXPIRED or contract removed |
| `resource_node_depleted` | event_extractor | EconomyScorer | 0 | Node remaining_charges drops to 0 |
| `region_trauma_delta` | event_extractor | WorldDynamicsScorer | 11 | Non-zero trauma_delta on world_updates |
| `region_ownership_changed` | event_extractor | WorldDynamicsScorer | 0 | owner_faction_id_set changes |
| `region_transformed` | event_extractor | WorldDynamicsScorer | 0 | kind_set on region update |
| `calamity_spawned` | event_extractor | WorldDynamicsScorer | 0 | last_calamity_tick_set == tick |
| `boss_spawned` | event_extractor | WorldDynamicsScorer | 0 | world-boss-gated: entity kind in (world_boss, ancient_sentinel) |
| `narrative_milestone` | event_extractor | NarrativeScorer | 0 | Co-emitted on boss_spawned, war_declared, sovereignty_shift |
| `raid_party_spawned` | event_extractor | WorldDynamicsScorer | 0 | goblin-raider-gated: entity kind == goblin_raider |
| `diplomatic_transition` | event_extractor | FactionScorer | 0 | Direct emit on faction diplomatic_relations_set change |
| `alliance_accepted` | event_extractor | FactionScorer | 0 | Direct emit when new_state == ALLIED |
| `territory_ownership_changed` | event_extractor | FactionScorer | 0 | faction.territory_add |
| `faction_tension_delta` | event_extractor | FactionScorer | 0 | Non-zero tension_delta on faction update |
| `war_declared` | event_extractor | FactionScorer | 0 | WorldEvent category == FACTION_WAR_DECLARED |
| `military_conflict_resolved` | event_extractor | FactionScorer | 0 | WorldEvent in (TERRITORY_TRANSFERRED, WAR_ENDED_EXHAUSTION) |
| `world_emergence_event` | event_extractor | NarrativeScorer | 0 | Every WorldEvent in world_events_add |
| `faction_extinct` | event_extractor | FactionScorer | 0 | Faction has no living members; fires only when faction_updates present |
| `chronicle_entry_created` | campaigns/narrative_ledger, campaigns/orchestrator | NarrativeScorer | 0 | Campaign-gated (see §4) |
| `quest_completed` | campaigns/runner | NarrativeScorer | 0 | Campaign-gated; also reachable via quest_event conditional translation |
| `scenario_objective_completed` | engine/scenario_runtime | NarrativeScorer | 0 | Scenario-gated (see §4) |
| `scenario_stalled` | engine/scenario_runtime | NarrativeScorer | 0 | Scenario-gated (see §4) |

### §1.2 Via `_TRANSLATE_SIMPLE` (one-to-one remaps)

| engine event_type | translation | contract_type | scorers | calibration_hits |
|---|---|---|---|---|
| `combat_kill` | _TRANSLATE_SIMPLE | `entity_killed` | CombatScorer | 1 |
| `gold_transaction` | _TRANSLATE_SIMPLE | `gold_transferred` | EconomyScorer | 0 |
| `StrategicObjectiveChanged` | _TRANSLATE_SIMPLE | `strategic_goal_changed` | CognitionScorer | 0 |
| `StrategicConcernRaised` | _TRANSLATE_SIMPLE | `strategic_goal_changed` | CognitionScorer | 0 |
| `StrategicDetourCreated` | _TRANSLATE_SIMPLE | `project_started` | AgencyScorer | 0 |
| `StrategicLeadExhausted` | _TRANSLATE_SIMPLE | `knowledge_default_fallback` | CognitionScorer | 0 |
| `leadership_changed` | _TRANSLATE_SIMPLE | `diplomatic_transition` | FactionScorer | 0 |
| `alliance_formed` | _TRANSLATE_SIMPLE | `alliance_accepted` | FactionScorer | 0 |

### §1.3 Via `_TRANSLATE_CONDITIONAL` (payload-conditional remaps)

| engine event_type | condition | contract_type | scorers | calibration_hits |
|---|---|---|---|---|
| `quest_event` | payload.status == "started" (default) | `quest_started` | NarrativeScorer | 233 |
| `quest_event` | payload.status == "completed" | `quest_completed` | NarrativeScorer | 0 |
| `quest_event` | payload.status == "failed" | `quest_failed` | NarrativeScorer | 0 |
| `lifecycle` | payload.action == "level_up" | `level_up` | ProgressionScorer | 0 |
| `lifecycle` | payload.action in ("despawn","death") | `entity_killed` | CombatScorer | 0 |
| `lifecycle` | payload.action == "spawn" | passthrough — no translation | none | 0 |
| `StrategicProjectChanged` | "complet" in reason | `project_completed` | AgencyScorer | 0 |
| `StrategicProjectChanged` | "abandon" in reason | `project_abandoned` | AgencyScorer | 0 |
| `StrategicProjectChanged` | default | `project_started` | AgencyScorer | 0 |
| `InvariantViolation` | law_id starts with "COMBAT" | `combat_hard_law_violation` | CombatScorer | 0 |
| `InvariantViolation` | law_id starts with "CONSERVATION" | `conservation_law_violated` | EconomyScorer | 0 |
| `InvariantViolation` | other law_id | passthrough — no translation | none | 0 |
| `betrayal_desertion` | payload.faction_id present | `faction_tension_delta` | FactionScorer | 0 |
| `betrayal_desertion` | no faction_id | `contract_lapsed` | SocialScorer | 0 |

---

## §2 Translation Gaps

**None found.** All 8 `_TRANSLATE_SIMPLE` entries and all 5 `_TRANSLATE_CONDITIONAL` entries in `src/simulation_quality/quality_hub.py` are correct and complete as of this audit. Every engine event_type that the translation table touches maps to a valid contract vocabulary type that exists in `SCORER_REGISTRY`.

Test coverage was incomplete for 3 entries (`leadership_changed`, `alliance_formed`, `betrayal_desertion`). Tests were added in `tests/simulation_quality/test_quality_hub_event_translation.py` as part of this ticket.

---

## §3 Engine Emission Gaps

These contract vocabulary types appear in at least one scorer's `EVENT_TYPES` tuple and are therefore registered in `SCORER_REGISTRY`, but the engine never emits them. Scoring infrastructure is ready; upstream emission is deferred to future engine work.

### §3.1 Agency (AgencyScorer)

| contract_type | notes |
|---|---|
| `defer_with_reason` | Defined in `src/domains/adventure/schema.py` as DEFER_WITH_REASON; engine currently embeds this in the `route_selected` payload.family field rather than emitting it as a separate event |
| `commitment_abandoned` | No engine emitter found |
| `rejection_cascade_tick` | No engine emitter found |
| `route_family_first_use` | No engine emitter found; expected to fire once per novel routing family per entity |

### §3.2 Cognition (CognitionScorer)

| contract_type | notes |
|---|---|
| `decision_divergence_detected` | No engine emitter found |

### §3.3 Information (InformationScorer)

| contract_type | notes |
|---|---|
| `lead_certainty_updated` | Per contract §5 (line 756), this is a DISTINCT event from `lead_certainty_changed` (CognitionScorer). The engine emits `lead_certainty_changed` for raw state diffs; `lead_certainty_updated` is intended to represent a post-processed knowledge update. Engine does not yet emit this separate event. |
| `lead_contradiction_resolved` | No engine emitter found; emitter location: `src/engine/pipeline_phases/lead_contradiction.py` emits `belief_contradiction` (different event) |
| `paid_info_changed_goal` | No engine emitter found |
| `belief_stale` | No engine emitter found |
| `decision_diverged_by_belief` | No engine emitter found |

### §3.4 Economy (EconomyScorer)

| contract_type | notes |
|---|---|
| `paid_info_transaction` | Per contract §5 (line 625), this is the ECONOMY-pillar event for information purchases (separate from `paid_information_transaction` which is the INFORMATION-pillar event). Engine only emits `paid_information_transaction` via event_extractor. Adding `paid_info_transaction` requires a second emit in event_extractor when src_kind==INFORMATION_PURCHASE. |
| `conservation_law_verified` | No engine emitter found; conservation law is checked but passing verification is not emitted |

### §3.5 Narrative (NarrativeScorer)

| contract_type | notes |
|---|---|
| `scenario_objective_progressed` | `engine/scenario_runtime.py` only emits `scenario_objective_completed`; there is no intermediate progress event emitted |

### §3.6 Progression (ProgressionScorer)

| contract_type | notes |
|---|---|
| `skill_unlocked` | No engine emitter found |
| `trait_expressed` | No engine emitter found |
| `pillar_trait_unlocked` | No engine emitter found |
| `progression_conversion_applied` | No engine emitter found |
| `progression_plateau_detected` | No engine emitter found |

### §3.7 Faction (FactionScorer)

| contract_type | notes |
|---|---|
| `alliance_proposed` | No engine emitter found; alliance_accepted is emitted when ALLIED state is confirmed |
| `resource_seized` | No engine emitter found |

### §3.8 Social (SocialScorer)

| contract_type | notes |
|---|---|
| `social_memory_created` | No engine emitter found |
| `contract_milestone_completed` | No engine emitter found |

### §3.9 World Dynamics (WorldDynamicsScorer)

| contract_type | notes |
|---|---|
| `ecology_cycle_completed` | No engine emitter found (comment in economy.py: "owned by WorldDynamicsScorer per SQ-08") |
| `spawn_cadence_fired` | No engine emitter found |
| `camp_constructed` | No engine emitter found |
| `threat_evolved` | No engine emitter found |
| `node_recharged` | No engine emitter found |

---

## §4 P0-A Blocked

Events in `SCORER_REGISTRY` that are not emitted in calibration runs because the subsystem that generates them (campaigns layer, scenario mode) is not active in sandbox_world/dungeon_crawl/wilderness_survival calibration scenarios.

These events DO pass through the translation layer correctly when the subsystem is active and WILL be scored. They are not engine emission gaps — they would appear in full campaign or scenario-mode runs.

| event_type | blocking gate | scorers |
|---|---|---|
| `chronicle_entry_created` | campaigns layer not active in calibration | NarrativeScorer |
| `scenario_objective_completed` | scenario mode not active in calibration | NarrativeScorer |
| `scenario_stalled` | scenario mode not active in calibration | NarrativeScorer |

Note: `boss_spawned` and `raid_party_spawned` are world-infrastructure-gated (require specific entity kinds), but they ARE emitted when those entities spawn. They are classified as `scored` (§1.1) since the engine path exists.

---

## §5 Unscored Intentional

Events emitted by the engine that are deliberately NOT routed to any scorer. No action required.

| event_type | source | reason |
|---|---|---|
| `movement` | MovementEvent | High-volume positional data; not a quality signal |
| `lifecycle` (spawn action) | LifecycleEvent | Spawn passthrough — no quality contract for raw spawn |
| `resource_node_regenerated` | event_extractor | Not a quality signal; node recharge tracked separately |
| `LEGENDARY_ARRIVAL` | LegendaryArrivalEvent | Social consequence event; quality signal not yet defined |
| `KNOWN_TRAITOR_SPOTTED` | KnownTraitorSpottedEvent | Social consequence event; quality signal not yet defined |
| `OLD_DEBT_COLLECTED` | OldDebtCollectedEvent | Social consequence event; quality signal not yet defined |
| `REFINED_UPDATE` | engine/kernel | Kernel internal; pipeline phase marker |
| `GovernorModeChanged` | engine/kernel | Kernel internal; governance state change |
| `TICK_END` | engine/kernel | Kernel internal; tick lifecycle marker |
| `InvariantViolation` (unknown law) | engine/kernel | Falls through conditional translator; unknown law ID has no contract type |
| `belief_contradiction` | engine/pipeline_phases/lead_contradiction | Not yet wired to quality scoring |
| `plan_revision` | campaigns/plan_revision | Campaign planning artifact; not a simulation quality signal |
| `DEFLATION_RISK`, `INFLATION_SPIRAL`, `ECONOMIC_COLLAPSE`, `GOLD_HOARDING` | EconomyHealthMonitor | Defined in events.py but marked deferred — not yet emitted |

---

## §6 Maintenance Notes

- When adding a new `event_type` to `event_extractor.py` or any domain emitter, check this table first.
- If the event should be scored, either: (a) use contract vocabulary directly, or (b) add a `_TRANSLATE_SIMPLE` / `_TRANSLATE_CONDITIONAL` entry to `quality_hub.py` and update this table.
- Engine emission gap events (§3) are the primary expansion surface for future SimQ coverage.
- The `paid_info_transaction` / `lead_certainty_updated` gaps (§3.3, §3.4) require new emit calls in `event_extractor.py` — these should be tracked as follow-on tickets.
- Run `make knowledge-index-update` after any change to docs in this directory.
