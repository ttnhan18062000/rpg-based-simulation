---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Phase 11 — Cognition Hierarchy Restructure

# Goal

Restructure the growing flat aspect list into a stable hierarchy.

The target is:

```text
EntityState
  factual components
  cognition
    subjective
    memory
    motivation
    commitment
    relationships
```

This phase should **not** add major new behavior yet. It creates the structure that future aspects can live inside.

---

# Success definition

Phase 11 is successful when entity cognition is no longer scattered like this:

```text
entity.self_awareness
entity.need_interpretation
entity.knowledge_model
entity.risk_belief
entity.temporal_awareness
entity.emotion
entity.causal_memory
entity.spatial_memory
...
```

but organized like this:

```text
entity.cognition.subjective.self
entity.cognition.subjective.knowledge
entity.cognition.subjective.risk
entity.cognition.memory.causal
entity.cognition.memory.spatial
entity.cognition.motivation.doctrine
entity.cognition.commitment.active_commitments
entity.cognition.relationships.private_trust
```

---

# Task 1 — Define `CognitionModel`

## Description

Add one wrapper model that becomes the only top-level cognition entry point.

```python
@dataclass(frozen=True)
class CognitionModel:
    subjective: SubjectiveModel = field(default_factory=SubjectiveModel)
    memory: MemoryModel = field(default_factory=MemoryModel)
    motivation: MotivationModel = field(default_factory=MotivationModel)
    commitment: CommitmentModel = field(default_factory=CommitmentModel)
    relationships: RelationshipModel = field(default_factory=RelationshipModel)
```

## Checklist

- [ ] `EntityState` has `cognition: CognitionModel`.
- [ ] Default construction works.
- [ ] Frozen/immutable pattern matches current state style.
- [ ] No domain-specific “adventure readiness” field is stored.
- [ ] All submodels have safe empty defaults.
- [ ] Serialization is deterministic.
- [ ] Canonical hash behavior is documented.
- [ ] Builder supports `.cognition(...)`.
- [ ] Existing entities can be created without manually passing cognition.

## Tests

```text
tests/unit/entity/test_phase11_cognition_model_schema.py
```

Test cases:

```text
test_entity_state_has_default_cognition_model
test_cognition_model_default_is_empty_and_safe
test_cognition_model_serializes_deterministically
test_entity_builder_can_set_cognition_model
test_cognition_model_does_not_require_adventure_fields
```

---

# Task 2 — Define `SubjectiveModel`

## Description

This contains current subjective interpretation.

```python
@dataclass(frozen=True)
class SubjectiveModel:
    perception: PerceptionModel = field(default_factory=PerceptionModel)
    self: SelfModel = field(default_factory=SelfModel)
    knowledge: KnowledgeModel = field(default_factory=KnowledgeModel)
    risk: RiskModel = field(default_factory=RiskModel)
    time: TemporalModel = field(default_factory=TemporalModel)
    emotion: EmotionalModel = field(default_factory=EmotionalModel)
```

## Meaning

```text
SubjectiveModel = what the entity currently notices, believes, feels, estimates, and prioritizes.
```

## Checklist

- [ ] `PerceptionModel` exists as empty shell.
- [ ] `SelfModel` wraps existing self-awareness/needs/capability.
- [ ] `KnowledgeModel` wraps facts, unknowns, beliefs, leads, source trust.
- [ ] `RiskModel` exists as empty shell.
- [ ] `TemporalModel` exists as empty shell.
- [ ] `EmotionalModel` exists as empty shell.
- [ ] Existing Phase 2 fields are mapped into this hierarchy.
- [ ] No flat duplicate fields are needed long-term.

## Tests

```text
tests/unit/entity/test_phase11_subjective_model_schema.py
```

Test cases:

```text
test_subjective_model_contains_perception_self_knowledge_risk_time_emotion
test_subjective_model_defaults_are_empty
test_existing_self_model_bundle_can_be_embedded
test_knowledge_model_supports_facts_unknowns_beliefs_leads_source_trust
```

---

# Task 3 — Define `SelfModel`

## Description

Move current Phase 2 self-model outputs under one submodel.

```python
@dataclass(frozen=True)
class SelfModel:
    awareness: SelfAwarenessComponent = field(default_factory=SelfAwarenessComponent)
    needs: NeedInterpretationComponent = field(default_factory=NeedInterpretationComponent)
    capability: CapabilityEstimateComponent = field(default_factory=CapabilityEstimateComponent)
    recovery: RecoveryState = field(default_factory=RecoveryState)
```

## Checklist

- [ ] `SelfAwarenessComponent` is no longer conceptually top-level.
- [ ] `NeedInterpretationComponent` is nested under `self`.
- [ ] `CapabilityEstimateComponent` is nested under `self`.
- [ ] `RecoveryState` placeholder exists but can be empty.
- [ ] Existing self assessment services write to `cognition.subjective.self`.
- [ ] Existing tests are updated to read through the new path.

## Tests

```text
tests/unit/entity/test_phase11_self_model_migration.py
```

Test cases:

```text
test_self_awareness_access_through_cognition_subjective_self
test_need_interpretation_access_through_cognition_subjective_self
test_capability_estimate_access_through_cognition_subjective_self
test_self_model_update_writes_new_cognition_path
```

---

# Task 4 — Define `MemoryModel`

## Description

Memory should be separated from current subjective state.

```python
@dataclass(frozen=True)
class MemoryModel:
    experience: ExperienceMemory = field(default_factory=ExperienceMemory)
    causal: CausalMemory = field(default_factory=CausalMemory)
    spatial: SpatialMemory = field(default_factory=SpatialMemory)
    habit: HabitMemory = field(default_factory=HabitMemory)
    combat: CombatMemory = field(default_factory=CombatMemory)
    social: SocialMemory = field(default_factory=SocialMemory)
```

## Checklist

- [ ] Memory model exists with empty defaults.
- [ ] No memory list is unbounded.
- [ ] Each memory submodel has capacity config placeholder.
- [ ] Memory is historical, not current belief.
- [ ] Knowledge facts remain under `SubjectiveModel.knowledge`.
- [ ] Combat opponent models can later live under `memory.combat`.
- [ ] Cooperation history can later live under `memory.social`.

## Tests

```text
tests/unit/entity/test_phase11_memory_model_schema.py
```

Test cases:

```text
test_memory_model_defaults_are_empty
test_memory_model_contains_causal_spatial_habit_combat_social
test_memory_model_capacity_fields_exist
test_memory_model_serializes_deterministically
```

---

# Task 5 — Define `MotivationModel`

## Description

This stores long-term values and identity bias.

```python
@dataclass(frozen=True)
class MotivationModel:
    doctrine: IdentityDoctrine = field(default_factory=IdentityDoctrine)
    values: ValuePreferenceProfile = field(default_factory=ValuePreferenceProfile)
    role_fit: RoleFitPreference = field(default_factory=RoleFitPreference)
    ambition: AmbitionProfile = field(default_factory=AmbitionProfile)
    moral: MoralPreferenceProfile = field(default_factory=MoralPreferenceProfile)
```

## Checklist

- [ ] Motivation model exists.
- [ ] Class/role preference can be represented.
- [ ] Values can bias route selection.
- [ ] Moral preference exists as light bias only.
- [ ] Motivation is stable and not updated every tick.
- [ ] Personality/traits can be mapped into motivation later.
- [ ] No decision service directly mutates motivation without update path.

## Tests

```text
tests/unit/entity/test_phase11_motivation_model_schema.py
```

Test cases:

```text
test_motivation_model_defaults_are_empty
test_doctrine_can_represent_class_route_preference
test_values_can_represent_survival_reward_knowledge_social_bias
test_motivation_model_serializes_deterministically
```

---

# Task 6 — Define `CommitmentModel`

## Description

This stores promises, obligations, accepted commitments, and abandonment records.

```python
@dataclass(frozen=True)
class CommitmentModel:
    active_commitments: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    quest_obligations: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    contract_obligations: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    party_obligations: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    abandoned_commitments: tuple[AbandonedCommitmentEntry, ...] = ()
```

## Checklist

- [ ] Commitment model exists.
- [ ] Quest obligations can be represented.
- [ ] Contract obligations can be represented.
- [ ] Party obligations can be represented.
- [ ] Abandoned commitments can be recorded.
- [ ] Commitment pressure can be computed later.
- [ ] No direct action execution happens from commitment model.

## Tests

```text
tests/unit/entity/test_phase11_commitment_model_schema.py
```

Test cases:

```text
test_commitment_model_defaults_are_empty
test_commitment_model_can_store_quest_obligation
test_commitment_model_can_store_contract_obligation
test_commitment_model_can_store_abandoned_commitment
test_commitment_model_serializes_deterministically
```

---

# Task 7 — Define `RelationshipModel`

## Description

Separate private relationship from public reputation.

```python
@dataclass(frozen=True)
class RelationshipModel:
    private_trust: Mapping[int, TrustEntry] = field(default_factory=dict)
    public_reputation: PublicReputationProfile = field(default_factory=PublicReputationProfile)
    known_partners: Mapping[int, PartnerMemory] = field(default_factory=dict)
    betrayal_records: tuple[BetrayalRecord, ...] = ()
```

## Checklist

- [ ] Private trust and public reputation are separate.
- [ ] Partner memory can be represented.
- [ ] Betrayal records are bounded.
- [ ] Existing `social` component is not broken.
- [ ] Existing social contract tests continue to pass.
- [ ] Relationship model can later feed cooperation.

## Tests

```text
tests/unit/entity/test_phase11_relationship_model_schema.py
```

Test cases:

```text
test_relationship_model_defaults_are_empty
test_private_trust_is_separate_from_public_reputation
test_partner_memory_can_be_recorded
test_betrayal_records_are_bounded
```

---

# Task 8 — Add compatibility accessors

## Description

To avoid rewriting the entire codebase in one step, add compatibility helpers.

Example:

```python
def get_self_awareness(entity: EntityState) -> SelfAwarenessComponent:
    return entity.cognition.subjective.self.awareness
```

## Checklist

- [ ] Accessor functions exist for old common paths.
- [ ] No direct mutation through accessors.
- [ ] Deprecated old paths are documented.
- [ ] Tests use new paths where possible.
- [ ] Domain services migrate gradually.
- [ ] Compatibility layer has clear removal plan.

## Tests

```text
tests/unit/entity/test_phase11_cognition_accessors.py
```

Test cases:

```text
test_get_self_awareness_reads_new_path
test_get_knowledge_model_reads_new_path
test_get_causal_memory_reads_new_path
test_accessors_do_not_mutate_entity
```

---

# Task 9 — Update builder API

## Description

The builder should support both broad and focused cognition construction.

Example:

```python
builder.cognition(...)
builder.subjective(...)
builder.memory(...)
builder.motivation(...)
builder.commitment(...)
```

## Checklist

- [ ] `.cognition()` method exists.
- [ ] `.subjective()` method exists.
- [ ] `.memory()` method exists.
- [ ] `.motivation()` method exists.
- [ ] `.commitment()` method exists.
- [ ] Existing builder calls still work during migration.
- [ ] New builder methods do not duplicate many conflicting aliases.

## Tests

```text
tests/unit/builder/test_phase11_cognition_builder.py
```

Test cases:

```text
test_builder_can_set_full_cognition_model
test_builder_can_set_subjective_model
test_builder_can_set_memory_model
test_builder_can_set_motivation_model
test_builder_can_set_commitment_model
test_builder_defaults_cognition_when_not_provided
```

---

# Task 10 — Update canonical serialization / hashing

## Description

Decide whether cognition affects authoritative state hash.

Recommended:

```text
If cognition affects future decisions, include it.
If trace-only diagnostics, exclude it.
```

For this architecture, cognition should usually be authoritative because it affects future choices.

## Checklist

- [ ] Cognition hash inclusion is explicit.
- [ ] Empty cognition has stable hash.
- [ ] Equivalent cognition serializes identically.
- [ ] SHADOW-only cognition output does not pollute authoritative hash.
- [ ] ON-mode cognition updates can affect hash deterministically.
- [ ] Existing observability parity tests are not broken.

## Tests

```text
tests/certification/test_phase11_cognition_hashing.py
```

Test cases:

```text
test_empty_cognition_hash_is_stable
test_equivalent_cognition_models_have_same_hash
test_shadow_cognition_diagnostics_do_not_change_hash
test_on_mode_cognition_update_changes_hash_deterministically
```

---

# Task 11 — Migration audit

## Description

Add a check that prevents accidental new flat cognition fields.

## Rule

Bad:

```python
entity.temporal_awareness
entity.causal_memory
entity.emotional_state
```

Good:

```python
entity.cognition.subjective.time
entity.cognition.memory.causal
entity.cognition.subjective.emotion
```

## Checklist

- [ ] Static test detects forbidden flat cognition fields.
- [ ] Allowed factual fields are whitelisted.
- [ ] New cognition fields must be inside `CognitionModel`.
- [ ] Failure message explains correct path.
- [ ] Test can be updated intentionally when schema changes.

## Tests

```text
tests/architecture/test_phase11_no_flat_cognition_fields.py
```

Test cases:

```text
test_entity_state_does_not_add_new_flat_cognition_fields
test_cognition_fields_live_under_cognition_model
```

---

# Phase 11 non-goals

Do not implement full behavior for:

```text
attention
emotion
causal memory
spatial memory
habit memory
reputation
commitment pressure
```

Only create the hierarchy and migrate existing self-model/knowledge structures.

---

# Phase 11 completion criteria

```text
Entity cognition has one readable root.
Existing self-model data lives under the new hierarchy.
Builder, serialization, hashing, and tests support the hierarchy.
No new flat cognition fields are allowed.
```

---

# Phase 12 — Perception / Attention Domain

# Goal

Prevent entity omniscience.

Entities should not evaluate every visible/world object equally. They should notice, miss, prioritize, and ignore signals based on condition, traits, goals, danger, and familiarity.

---

# Success definition

Given the same environment:

```text
forest contains herb, wolf tracks, cave entrance, traveler, loot clue
```

different entities can notice different things:

```text
injured entity -> notices herb
cautious entity -> notices wolf tracks
curious entity -> notices cave entrance
greedy entity -> notices loot clue
social entity -> notices traveler
```

---

# Task 1 — Define `PerceptionModel`

```python
@dataclass(frozen=True)
class PerceptionModel:
    attention_focus: tuple[str, ...] = ()
    perceived_entities: Mapping[int, PerceivedEntity] = field(default_factory=dict)
    perceived_resources: Mapping[str, PerceivedResource] = field(default_factory=dict)
    perceived_services: Mapping[str, PerceivedService] = field(default_factory=dict)
    perceived_threats: Mapping[str, PerceivedThreat] = field(default_factory=dict)
    perceived_opportunities: Mapping[str, PerceivedOpportunity] = field(default_factory=dict)
    ignored_signals: tuple[IgnoredSignal] = ()
    last_updated_tick: int = 0
```

## Checklist

- [ ] Perception model exists under `cognition.subjective.perception`.
- [ ] Perceived facts are not world truth.
- [ ] Perceived objects include confidence/salience.
- [ ] Ignored signals can be recorded for debugging.
- [ ] Perception entries are bounded.
- [ ] Serialization is deterministic.

## Tests

```text
tests/unit/entity/test_phase12_perception_model.py
```

Test cases:

```text
test_perception_model_defaults_are_empty
test_perceived_entity_has_confidence_and_salience
test_ignored_signal_can_be_recorded
test_perception_entries_are_bounded
```

---

# Task 2 — Implement `AttentionFocusService`

## Description

This computes what the entity is currently biased to notice.

Inputs:

```text
dominant need
active project
emotion
risk memory
motivation
current region
recent events
```

Outputs:

```text
attention focus tags
```

Examples:

```text
low_health -> healing_resource, healer, safe_place
equipment_gap -> blacksmith, weapon, material
fear -> threat, escape_route, ally
curiosity -> clue, unknown_location, rumor
```

## Tests

```text
tests/unit/domains/perception/test_phase12_attention_focus_service.py
```

Test cases:

```text
test_low_health_focuses_on_healing_and_safety
test_equipment_gap_focuses_on_gear_and_materials
test_active_information_need_focuses_on_sources_and_clues
test_fear_focuses_on_threats_and_escape
test_attention_focus_is_deterministic
```

---

# Task 3 — Implement `SignalSalienceEvaluator`

## Description

Rank world signals by salience.

Signal examples:

```text
nearby enemy
rare resource
known quest target
trusted ally
wounded stranger
service building
danger rumor
```

Scoring idea:

```text
salience =
  relevance_to_need
  + relevance_to_project
  + danger
  + novelty
  + familiarity
  + motivation_bias
  - distance_penalty
  - overload_penalty
```

## Tests

```text
tests/unit/domains/perception/test_phase12_signal_salience_evaluator.py
```

Test cases:

```text
test_nearby_threat_has_high_salience
test_resource_needed_for_active_recipe_has_high_salience
test_far_irrelevant_signal_has_low_salience
test_novel_signal_gets_curiosity_bonus
test_overload_reduces_low_priority_signal_salience
```

---

# Task 4 — Implement `PerceptionFilterService`

## Description

Convert scoped world signals into perceived signals.

It should not scan the whole world.

```python
class PerceptionFilterService:
    def filter(
        self,
        entity: EntityState,
        candidate_signals: Sequence[WorldSignal],
        budget: PerceptionBudget,
    ) -> PerceptionUpdate:
        ...
```

## Checklist

- [ ] Accepts scoped candidate signals only.
- [ ] Applies salience scoring.
- [ ] Applies attention focus.
- [ ] Applies perception capacity.
- [ ] Records ignored high-value signals only when useful.
- [ ] Does not reveal hidden exact truth.
- [ ] Deterministic ordering.

## Tests

```text
tests/unit/domains/perception/test_phase12_perception_filter_service.py
```

Test cases:

```text
test_filter_keeps_high_salience_signals
test_filter_drops_low_salience_signals_when_capacity_full
test_filter_does_not_reveal_hidden_truth
test_filter_respects_perception_budget
test_filter_output_order_is_deterministic
```

---

# Task 5 — Add perception update phase

## Trigger conditions

```text
entity moved
entered region
new world signal nearby
danger event occurred
information source nearby
active project changed
dominant need changed
```

## Skip conditions

```text
entity dead/inactive
no candidate signals
perception cooldown active
budget exhausted
feature flag disabled
```

## Tests

```text
tests/integration/domains/perception/test_phase12_perception_phase.py
```

Test cases:

```text
test_phase_runs_when_entity_enters_new_region
test_phase_skips_clean_entity
test_phase_updates_perception_model
test_phase_does_not_full_scan_world
test_phase_respects_feature_flag
```

---

# Task 6 — Add perception scenario tests

## Scenario 12.1 — Injured entity notices healing

Expected:

```text
low HP entity notices herb/healer before loot clue
```

## Scenario 12.2 — Cautious entity notices danger

Expected:

```text
cautious entity notices wolf tracks and avoids/probes
```

## Scenario 12.3 — Perception prevents hidden knowledge

Expected:

```text
entity cannot route to hidden cave unless perceived clue exists
```

## Scenario 12.4 — Attention overload drops weak signal

Expected:

```text
when many signals exist, only top salience signals enter perception
```

## Test file

```text
tests/integration/scenarios/test_phase12_perception_attention_scenarios.py
```

---

# Phase 12 non-goals

Do not implement:

```text
visual cone simulation
line-of-sight geometry
stealth system
complex sensory physics
global perception graph
```

This is salience and attention, not physics.

---

# Completion criteria

```text
Entity decisions can only use signals that entered perception, knowledge, memory, or direct local observation.
```

Minimum proof:

```text
different entities notice different things
hidden signals are not used
perception is capacity-bounded
perception changes route/combat/information behavior
```

---

# Phase 13 — Temporal / Causal / Spatial Memory Domain

# Goal

Give entities continuity across time, place, and cause.

This phase implements:

```text
TemporalModel
CausalMemory
SpatialMemory
```

These three should be implemented together because they answer:

```text
When did this happen?
Where did this happen?
Why did I think it happened?
```

---

# Success definition

After a failed wolf fight:

```text
entity remembers:
- it happened in wolf_den
- it happened recently
- it likely failed because weapon was damaged and stamina was low
```

Future behavior:

```text
repair weapon before retry
avoid wolf_den while wounded
return later when stronger
```

---

# Task 1 — Define `TemporalModel`

```python
@dataclass(frozen=True)
class TemporalModel:
    deadlines: Mapping[str, DeadlineEntry] = field(default_factory=dict)
    cooldowns: Mapping[str, CooldownEntry] = field(default_factory=dict)
    stale_facts: Mapping[str, StalenessEntry] = field(default_factory=dict)
    urgency: Mapping[str, float] = field(default_factory=dict)
    delay_risks: Mapping[str, DelayRiskEntry] = field(default_factory=dict)
```

## Tests

```text
tests/unit/entity/test_phase13_temporal_model.py
```

Test cases:

```text
test_temporal_model_defaults_are_empty
test_deadline_entry_can_be_recorded
test_cooldown_entry_can_be_recorded
test_stale_fact_entry_can_be_recorded
test_temporal_model_serializes_deterministically
```

---

# Task 2 — Implement `TemporalPressureService`

## Description

Converts deadlines/cooldowns/staleness into urgency pressure.

Examples:

```text
quest deadline soon -> urgency high
rumor old -> trust lower
combat reassessment cooldown active -> do not flicker
rest delay dangerous -> recover now
```

## Tests

```text
tests/unit/domains/time/test_phase13_temporal_pressure_service.py
```

Test cases:

```text
test_soon_deadline_increases_urgency
test_expired_deadline_invalidates_commitment
test_old_rumor_gets_staleness_penalty
test_active_cooldown_prevents_immediate_retry
test_delay_risk_can_raise_recovery_priority
```

---

# Task 3 — Define `CausalMemory`

```python
@dataclass(frozen=True)
class CausalMemoryEntry:
    event_id: str
    event_kind: str
    interpreted_causes: tuple[str, ...]
    confidence: float
    future_advice: tuple[str, ...]
    tick: int
    region_id: str | None = None

@dataclass(frozen=True)
class CausalMemory:
    entries: tuple[CausalMemoryEntry, ...] = ()
```

## Tests

```text
tests/unit/entity/test_phase13_causal_memory_model.py
```

Test cases:

```text
test_causal_memory_defaults_empty
test_causal_memory_entry_records_causes_and_future_advice
test_causal_memory_is_bounded
test_causal_memory_serializes_deterministically
```

---

# Task 4 — Implement `CausalAttributionService`

## Description

Interpret why something happened.

Supported events:

```text
combat_loss
near_death
failed_search
failed_craft
quest_failed
party_abandoned
resource_depleted
```

Example:

```text
combat_loss:
  possible causes:
    low_health
    low_stamina
    weak_weapon
    underestimated_enemy
    no_ally
```

## Tests

```text
tests/unit/domains/memory/test_phase13_causal_attribution_service.py
```

Test cases:

```text
test_combat_loss_attributes_low_stamina_and_damaged_weapon
test_failed_search_attributes_wrong_location_or_bad_rumor
test_failed_craft_attributes_missing_material_or_recipe
test_party_failure_attributes_abandonment_when_member_left
test_causal_attribution_does_not_claim_certainty_without_evidence
```

---

# Task 5 — Define `SpatialMemory`

```python
@dataclass(frozen=True)
class SpatialMemory:
    visited_regions: Mapping[str, RegionVisitMemory] = field(default_factory=dict)
    safe_routes: Mapping[str, RouteMemory] = field(default_factory=dict)
    dangerous_routes: Mapping[str, RouteMemory] = field(default_factory=dict)
    known_resource_sites: Mapping[str, ResourceSiteMemory] = field(default_factory=dict)
    failed_search_locations: Mapping[str, FailedSearchMemory] = field(default_factory=dict)
    home_base: str | None = None
```

## Tests

```text
tests/unit/entity/test_phase13_spatial_memory_model.py
```

Test cases:

```text
test_spatial_memory_defaults_empty
test_region_visit_memory_can_be_recorded
test_resource_site_memory_can_be_recorded
test_failed_search_location_can_be_recorded
test_home_base_can_be_recorded
```

---

# Task 6 — Implement `SpatialMemoryUpdateService`

## Description

Update spatial memory from movement, observation, search, and survival outcomes.

## Tests

```text
tests/unit/domains/memory/test_phase13_spatial_memory_update_service.py
```

Test cases:

```text
test_region_visit_updates_visit_count
test_safe_return_increases_region_familiarity
test_near_death_marks_region_dangerous
test_resource_observation_records_resource_site
test_failed_search_records_failed_location
```

---

# Task 7 — Add memory integration phase

## Trigger conditions

```text
combat result
search result
region entered/exited
resource observed
quest failed/completed
party outcome
information contradicted
```

## Tests

```text
tests/integration/domains/memory/test_phase13_memory_update_phase.py
```

Test cases:

```text
test_phase_updates_causal_memory_after_combat_loss
test_phase_updates_spatial_memory_after_region_visit
test_phase_updates_temporal_staleness_after_old_fact
test_phase_respects_memory_capacity
test_phase_respects_feature_flag
```

---

# Scenario tests

```text
tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py
```

Scenarios:

```text
lost_to_wolf_then_repairs_before_retry
failed_search_then_asks_other_source
safe_region_familiarity_reduces_travel_uncertainty
old_rumor_becomes_less_trusted
quest_deadline_changes_route_priority
```

---

# Completion criteria

```text
Entity remembers when, where, and why important events happened.
Future decisions use this memory.
```

---

# Phase 14 — Motivation / Doctrine / Role-Fit Domain [COMPLETE]

# Goal


Prevent all entities from converging into the same “optimal” route.

This phase makes long-term identity preferences explicit.

---

# Success definition

Given the same world and same objective pressure:

```text
warrior chooses weapon/combat route
ranger chooses scouting/resource route
mage chooses knowledge/skill route
cautious entity prepares first
proud entity avoids asking help
loyal entity protects ally
```

All choices must still be valid.

---

# Task 1 — Define `IdentityDoctrine`

```python
@dataclass(frozen=True)
class IdentityDoctrine:
    class_id: str | None = None
    preferred_route_tags: Mapping[str, float] = field(default_factory=dict)
    avoided_route_tags: Mapping[str, float] = field(default_factory=dict)
    combat_style_bias: Mapping[str, float] = field(default_factory=dict)
    cooperation_bias: Mapping[str, float] = field(default_factory=dict)
```

## Tests

```text
tests/unit/entity/test_phase14_identity_doctrine_model.py
```

---

# Task 2 — Define `ValuePreferenceProfile`

```python
@dataclass(frozen=True)
class ValuePreferenceProfile:
    survival: float = 0.5
    reward: float = 0.5
    knowledge: float = 0.5
    loyalty: float = 0.5
    pride: float = 0.5
    curiosity: float = 0.5
    caution: float = 0.5
```

## Tests

```text
tests/unit/entity/test_phase14_value_preference_model.py
```

Test cases:

```text
test_value_profile_defaults_neutral
test_value_profile_clamps_values
test_value_profile_serializes_deterministically
```

---

# Task 3 — Define `RoleFitPreference`

```python
@dataclass(frozen=True)
class RoleFitPreference:
    weapon_tags: Mapping[str, float] = field(default_factory=dict)
    armor_tags: Mapping[str, float] = field(default_factory=dict)
    skill_tags: Mapping[str, float] = field(default_factory=dict)
    party_role_tags: Mapping[str, float] = field(default_factory=dict)
    quest_tags: Mapping[str, float] = field(default_factory=dict)
```

## Tests

```text
tests/unit/entity/test_phase14_role_fit_preference_model.py
```

---

# Task 4 — Implement `DoctrineResolver`

## Description

Creates doctrine from class, role, traits, and optional scenario config.

Examples:

```text
warrior -> melee, armor, direct combat
ranger -> scouting, bow, tracking
mage -> knowledge, spell, rare materials
```

## Tests

```text
tests/unit/domains/motivation/test_phase14_doctrine_resolver.py
```

Test cases:

```text
test_warrior_doctrine_prefers_melee_combat
test_ranger_doctrine_prefers_scouting_and_ranged
test_mage_doctrine_prefers_knowledge_and_skill_growth
test_doctrine_resolver_is_deterministic
```

---

# Task 5 — Implement `RoleFitEvaluator`

## Description

Evaluate whether item/action/quest/partner fits the entity.

Inputs:

```text
item tags
skill tags
quest tags
party role tags
entity doctrine
current capability
```

## Tests

```text
tests/unit/domains/motivation/test_phase14_role_fit_evaluator.py
```

Test cases:

```text
test_warrior_prefers_sword_over_staff
test_mage_prefers_staff_over_sword_even_if_sword_raw_damage_higher
test_ranger_prefers_scouting_quest
test_role_fit_affects_partner_role_selection
test_role_fit_does_not_override_survival_need_when_critical
```

---

# Task 6 — Add motivation scoring adapter

## Description

Expose motivation bias to decision systems through one adapter.

```python
class MotivationBiasService:
    def route_bias(...)
    def combat_bias(...)
    def progression_bias(...)
    def cooperation_bias(...)
```

## Tests

```text
tests/unit/domains/motivation/test_phase14_motivation_bias_service.py
```

Test cases:

```text
test_survival_value_boosts_recovery_route
test_curiosity_value_boosts_information_route
test_loyalty_value_boosts_guard_ally
test_pride_value_penalizes_request_help
test_reward_value_boosts_gold_route
```

---

# Scenario tests

```text
tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py
```

Scenarios:

```text
same_world_classes_choose_different_valid_routes
mage_does_not_auto_equip_raw_stronger_sword
proud_entity_delays_help_request_when_risk_moderate
loyal_entity_interrupts_to_guard_ally
curious_entity_prefers_information_when_unknown_exists
```

---

# Completion criteria

```text
Entity choices diverge because of stable identity and values, not random noise.
```

---

# Phase 15 — Commitment / Obligation / Reputation Domain [COMPLETE]

# Goal


Make promises, contracts, accepted quests, party duties, and public reputation affect future behavior.

---

# Success definition

An entity that accepted an escort quest should not instantly abandon it for slightly better loot.

An entity that abandons others should face private trust loss and possible public reputation damage.

---

# Task 1 — Define `CommitmentEntry`

```python
@dataclass(frozen=True)
class CommitmentEntry:
    id: str
    kind: str
    subject: str
    target_id: str | int | None
    strength: float
    deadline_tick: int | None
    source: str
    status: str
    created_tick: int
```

## Tests

```text
tests/unit/entity/test_phase15_commitment_entry_model.py
```

---

# Task 2 — Implement `CommitmentPressureService`

## Description

Computes pressure to keep, pause, abandon, or fulfill commitments.

Factors:

```text
commitment strength
deadline
risk
reward
trust/reputation cost
survival need
opportunity cost
```

## Tests

```text
tests/unit/domains/commitment/test_phase15_commitment_pressure_service.py
```

Test cases:

```text
test_accepted_quest_creates_commitment_pressure
test_deadline_increases_commitment_pressure
test_critical_survival_need_can_override_commitment
test_minor_loot_does_not_override_strong_commitment
test_commitment_pressure_has_reason_trace
```

---

# Task 3 — Implement `AbandonmentEvaluator`

## Description

Not all abandonment is betrayal.

Examples:

```text
valid abandonment: near death, impossible objective
bad abandonment: leaving ally during danger for loot
```

## Tests

```text
tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py
```

Test cases:

```text
test_survival_abandonment_is_valid_or_low_penalty
test_greed_abandonment_has_high_penalty
test_party_abandonment_during_danger_creates_betrayal_record
test_impossible_objective_abandonment_creates_low_reputation_penalty
```

---

# Task 4 — Define `PublicReputationProfile`

```python
@dataclass(frozen=True)
class PublicReputationProfile:
    labels: Mapping[str, float] = field(default_factory=dict)
    witnessed_events: tuple[str, ...] = ()
    last_updated_tick: int = 0
```

Labels:

```text
reliable
reckless
cowardly
heroic
betrayer
monster_slayer
camp_clearer
failed_escort
known_crafter
```

## Tests

```text
tests/unit/entity/test_phase15_public_reputation_model.py
```

---

# Task 5 — Implement `ReputationUpdateService`

## Description

Updates public labels from witnessed/reportable events.

## Tests

```text
tests/unit/domains/reputation/test_phase15_reputation_update_service.py
```

Test cases:

```text
test_successful_escort_increases_reliable_reputation
test_party_abandonment_can_increase_betrayer_label
test_clearing_camp_increases_camp_clearer_label
test_unwitnessed_private_event_does_not_auto_become_public
test_reputation_updates_are_bounded
```

---

# Task 6 — Implement commitment/reputation route impact

## Description

Expose commitment/reputation as scoring modifiers.

Examples:

```text
accepted escort quest boosts escort objective
betrayer reputation lowers partner selection
heroic reputation increases recruitment success
```

## Tests

```text
tests/unit/domains/commitment/test_phase15_commitment_reputation_route_impact.py
```

Test cases:

```text
test_active_commitment_boosts_related_route
test_strong_commitment_penalizes_unrelated_route_switch
test_betrayer_reputation_penalizes_cooperation_candidate_score
test_reliable_reputation_boosts_party_acceptance
```

---

# Integration phase

```text
CommitmentReputationPhase:
  1. process accepted commitments
  2. evaluate abandonment/fulfillment
  3. update public/private consequences
  4. emit route impact hints
```

## Tests

```text
tests/integration/domains/commitment/test_phase15_commitment_reputation_phase.py
```

---

# Scenario tests

```text
tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py
```

Scenarios:

```text
accepted_escort_prevents_minor_loot_switch
critical_injury_allows_commitment_pause
abandoning_party_changes_future_partner_selection
successful_help_increases_public_reputation
unwitnessed_betrayal_affects_private_trust_not_public_reputation
```

---

# Completion criteria

```text
Commitments stabilize behavior.
Abandonment has explainable consequences.
Public reputation and private trust are separate.
```

---

# Phase 16 — Emotion / Recovery / Habit / Opportunity Cost Domain [COMPLETE]

# Goal


Make entities less robotic by adding short-term emotional bias, recovery state, learned habits, and explicit trade-off reasoning.

---

# Task 1 — Define `EmotionalModel`

```python
@dataclass(frozen=True)
class EmotionalModel:
    fear: float = 0.0
    confidence: float = 0.5
    frustration: float = 0.0
    curiosity: float = 0.0
    satisfaction: float = 0.0
    panic: float = 0.0
    boredom: float = 0.0
```

## Tests

```text
tests/unit/entity/test_phase16_emotional_model.py
```

---

# Task 2 — Implement `EmotionUpdateService`

## Events that affect emotion

```text
near_death -> fear/panic up
easy_win -> confidence up
repeated_failure -> frustration up
new_unknown -> curiosity up
successful_goal -> satisfaction up
stagnation -> boredom up
```

## Tests

```text
tests/unit/domains/emotion/test_phase16_emotion_update_service.py
```

Test cases:

```text
test_near_death_increases_fear_and_panic
test_easy_win_increases_confidence
test_repeated_failure_increases_frustration
test_new_unknown_increases_curiosity
test_successful_goal_increases_satisfaction
```

---

# Task 3 — Define `RecoveryState`

```python
@dataclass(frozen=True)
class RecoveryState:
    recent_near_death: bool = False
    confidence_loss: float = 0.0
    retry_readiness: float = 1.0
    recovery_until_tick: int | None = None
    trauma_tags: tuple[str, ...] = ()
```

## Tests

```text
tests/unit/entity/test_phase16_recovery_state_model.py
```

---

# Task 4 — Implement `RecoveryReadinessService`

## Description

Determines whether entity is ready to retry, recover, seek help, or choose easier content.

## Tests

```text
tests/unit/domains/recovery/test_phase16_recovery_readiness_service.py
```

Test cases:

```text
test_near_death_reduces_retry_readiness
test_rest_increases_retry_readiness
test_party_support_can_raise_retry_readiness
test_recovery_state_blocks_immediate_same_failed_retry
test_recovery_readiness_has_reason_trace
```

---

# Task 5 — Define `HabitMemory`

```python
@dataclass(frozen=True)
class HabitMemory:
    successful_patterns: Mapping[str, float] = field(default_factory=dict)
    failed_patterns: Mapping[str, float] = field(default_factory=dict)
    preferred_routes: Mapping[str, float] = field(default_factory=dict)
```

## Tests

```text
tests/unit/entity/test_phase16_habit_memory_model.py
```

---

# Task 6 — Implement `HabitBiasService`

## Examples

```text
crafting succeeded twice -> craft route bias
guide helped twice -> ask information bias
party betrayal -> cooperation route penalty
same failed route -> retry penalty
```

## Tests

```text
tests/unit/domains/habit/test_phase16_habit_bias_service.py
```

Test cases:

```text
test_successful_crafting_increases_future_craft_bias
test_successful_information_route_increases_future_information_bias
test_repeated_failed_route_creates_retry_penalty
test_habit_bias_is_bounded
test_habit_bias_does_not_override_critical_survival_need
```

---

# Task 7 — Implement `OpportunityCostEvaluator`

## Description

Explicitly compare what is lost by choosing a route.

Examples:

```text
sell iron now vs keep for sword
take quest now vs rest before deadline
join party now vs finish own quest
```

## Tests

```text
tests/unit/domains/decision/test_phase16_opportunity_cost_evaluator.py
```

Test cases:

```text
test_selling_needed_material_has_high_opportunity_cost
test_joining_party_can_conflict_with_active_commitment
test_resting_has_deadline_cost_when_quest_expires_soon
test_opportunity_cost_appears_in_decision_trace
```

---

# Integration phase

```text
EmotionRecoveryHabitPhase:
  1. update emotions from events
  2. update recovery state
  3. update habit memory
  4. expose route/scoring modifiers
```

## Tests

```text
tests/integration/domains/emotion/test_phase16_emotion_recovery_habit_phase.py
```

---

# Scenario tests

```text
tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py
```

Scenarios:

```text
near_death_prevents_immediate_retry
repeated_failure_causes_route_switch
successful_crafting_creates_craft_habit
frustration_causes_ask_help_or_abandon
opportunity_cost_prevents_selling_needed_material
```

---

# Completion criteria

```text
Entities recover, form habits, and account for trade-offs instead of repeating mechanical choices.
```

---

# Phase 17 — Derived Views / Decision Trace Contract [COMPLETE]

# Goal


Make all complex decisions inspectable and readable.

Do not store derived readiness as core state. Compute it.

---

# Task 1 — Define derived view builders

Views:

```text
AdventureReadinessView
CombatReadinessView
TravelReadinessView
CraftingReadinessView
CooperationReadinessView
RecoveryReadinessView
```

Each view should include:

```text
score
confidence
blocking factors
supporting factors
source aspects used
```

## Tests

```text
tests/unit/views/test_phase17_derived_readiness_views.py
```

Test cases:

```text
test_combat_readiness_view_uses_self_risk_memory_emotion
test_adventure_readiness_view_uses_self_knowledge_time_commitment
test_crafting_readiness_view_uses_knowledge_possession_role_fit
test_views_are_not_stored_as_core_entity_state
test_view_output_has_source_aspect_trace
```

---

# Task 2 — Define `DecisionTraceContract`

Every major decision must answer:

```text
what_did_i_notice
what_did_i_know
what_did_i_need
what_did_i_believe_i_could_do
what_options_were_considered
what_was_selected
what_was_rejected
why
what_changed_after_result
```

## Model

```python
@dataclass(frozen=True)
class DecisionTrace:
    decision_id: str
    entity_id: int
    decision_kind: str
    noticed: tuple[str, ...]
    known: tuple[str, ...]
    needs: tuple[str, ...]
    capability_refs: tuple[str, ...]
    considered_options: tuple[DecisionOptionTrace, ...]
    selected_option: str | None
    rejected_options: tuple[RejectedOptionTrace, ...]
    reason: str
    expected_effects: tuple[str, ...]
```

## Tests

```text
tests/unit/observability/test_phase17_decision_trace_contract.py
```

Test cases:

```text
test_decision_trace_requires_selected_or_defer_reason
test_decision_trace_requires_considered_options
test_decision_trace_requires_rejection_reasons
test_decision_trace_serializes_deterministically
```

---

# Task 3 — Apply trace contract to major domains

Domains:

```text
adventure decision
combat engagement
information query
progression conversion
cooperation decision
world signal response
```

## Tests

```text
tests/integration/observability/test_phase17_domain_decision_traces.py
```

Test cases:

```text
test_adventure_decision_emits_contract_trace
test_combat_engagement_emits_contract_trace
test_information_query_emits_contract_trace
test_progression_conversion_emits_contract_trace
test_cooperation_decision_emits_contract_trace
test_world_signal_response_emits_contract_trace
```

---

# Task 4 — Add trace validator

## Description

Reject or warn on incomplete traces.

Modes:

```text
OFF
WARN
STRICT
```

## Tests

```text
tests/unit/observability/test_phase17_decision_trace_validator.py
```

Test cases:

```text
test_validator_accepts_complete_trace
test_validator_rejects_trace_without_reason_in_strict_mode
test_validator_warns_in_warn_mode
test_validator_detects_selected_option_not_in_considered_options
```

---

# Task 5 — Add causality chain reporter

## Description

Show chain:

```text
perceived signal
-> belief/need
-> decision
-> action intent
-> authoritative result
-> memory/world update
-> future decision change
```

## Tests

```text
tests/unit/observability/test_phase17_causality_chain_reporter.py
```

Test cases:

```text
test_reporter_links_perception_to_decision
test_reporter_links_decision_to_action_result
test_reporter_links_result_to_memory_update
test_reporter_links_memory_to_future_decision
test_reporter_handles_missing_link_with_bounded_language
```

---

# Scenario tests

```text
tests/integration/scenarios/test_phase17_decision_trace_scenarios.py
```

Scenarios:

```text
combat_loss_has_full_causal_trace
information_route_has_full_causal_trace
reward_conversion_has_full_causal_trace
cooperation_betrayal_has_full_causal_trace
world_warning_changes_route_with_trace
```

---

# Completion criteria

```text
Every major behavior can be debugged from perception/knowledge/need to future behavior change.
```

---

# Phase 18 — Migration, Integration, and Architecture Guardrails [COMPLETE]

# Goal


Ensure the restructure does not create chaos.

This phase makes the new hierarchy safe to maintain.

---

# Task 1 — Architecture import boundaries

Rules:

```text
entity models cannot import domain services
domain services can import entity models
engine phases can import domain services
tests can import all
```

## Tests

```text
tests/architecture/test_phase18_import_boundaries.py
```

Test cases:

```text
test_entity_models_do_not_import_domain_services
test_domain_services_do_not_import_engine_kernel
test_observability_does_not_mutate_authoritative_state
```

---

# Task 2 — Domain ownership map

Create:

```text
docs/architecture/cognition_domain_ownership.md
```

Map:

```text
PerceptionModel -> domains/perception
TemporalModel -> domains/time
CausalMemory -> domains/memory
MotivationModel -> domains/motivation
CommitmentModel -> domains/commitment
RelationshipModel -> domains/cooperation/reputation
DerivedViews -> views/readiness
DecisionTrace -> observability/decision_trace
```

## Tests

```text
tests/architecture/test_phase18_domain_ownership_doc.py
```

---

# Task 3 — Migration linter

Detect:

```text
new flat cognition field
direct mutation of cognition submodel
domain service writing authoritative state directly
derived readiness stored as permanent field
```

## Tests

```text
tests/architecture/test_phase18_cognition_migration_linter.py
```

---

# Task 4 — Backward compatibility deprecation plan

Create:

```text
docs/migration/cognition_hierarchy_migration.md
```

Sections:

```text
old path
new path
temporary accessor
removal target
tests to update
```

---

# Task 5 — End-to-end hierarchy smoke test

Scenario:

```text
entity perceives danger
updates self/risk/time
chooses route
acts
records causal memory
future decision changes
trace validates
```

## Tests

```text
tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py
```

---

# Completion criteria

```text
The cognition hierarchy is enforceable, documented, migrated, and used by real domain services.
```

---

# Final roadmap summary

| Phase | Domain                                            |
| ----: | ------------------------------------------------- |
|    11 | Cognition hierarchy restructure                   |
|    12 | Perception / attention                            |
|    13 | Temporal / causal / spatial memory                |
|    14 | Motivation / doctrine / role fit                  |
|    15 | Commitment / obligation / reputation              |
|    16 | Emotion / recovery / habit / opportunity cost     |
|    17 | Derived views / decision trace contract           |
|    18 | Migration / integration / architecture guardrails |

---

# Implementation priority

Do in this order:

```text
1. Phase 11 — hierarchy restructure
2. Phase 17 — trace contract foundation
3. Phase 12 — perception / attention
4. Phase 13 — causal + spatial + temporal memory
5. Phase 14 — motivation / role fit
6. Phase 15 — commitment / reputation
7. Phase 16 — emotion / recovery / habit / opportunity cost
8. Phase 18 — final architecture guardrails
```

Reason:

```text
First organize cognition.
Then make decisions traceable.
Then prevent omniscience.
Then add memory and identity.
Then add obligation/reputation/emotion/habit.
Then lock the architecture.
```

The most important technical rule:

```text
Do not add more flat components.
Everything new must enter through CognitionModel or a derived view.
```
