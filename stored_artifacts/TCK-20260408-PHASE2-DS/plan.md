---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260408-PHASE2-DS
artifact_type: plan
tags: [phase2, ds]
---

# Phase 2 Implementation Plan — Social Meaning and Behavioral Realism

## Goal
Implement Phase 2 of the Macro-Interest design shift: convert raw events and memory into durable turning points, bounded relationships, public reputation, and readable life-level explanations. This is the "events now matter later" phase.

## Delivery Strategy — 5 Stages

Phase 2 uses the term **"stage"** for internal delivery milestones to avoid confusion with the overarching "phase" concept.

---

## Stage 1 — Core Social-History Models

### Objective
Add the four foundational data models that Phase 2 systems will consume and produce.

### Changes

#### [NEW] `src/core/models/life_events.py`
- `TurningPointKind` enum: `NEAR_DEATH`, `ALLY_DIED`, `AVENGED_ALLY`, `BETRAYAL`, `RESCUE`, `DISGRACE`, `REVENGE`, `HOME_LOST`, `BOSS_ENCOUNTER`, `FIRST_KILL`.
- `TurningPointRecord` model: `event_id`, `kind`, `tick`, `location`, `involved_entity_ids`, `summary_tag`, `emotional_impact`, `relationship_effects`, `motive_effects`, `still_salient`, `salience_score`.
- `InterpretedLifeEventKind` enum: `NEAR_DEATH`, `ALLY_DIED_NEARBY`, `AVENGED_ALLY`, `FLED_FROM_THREAT`, `HELD_POSITION`, `LOOTED_DURING_DANGER`, `FIRST_BOSS_ENCOUNTER`.
- `InterpretedLifeEvent` model: `event_id`, `kind`, `tick`, `actor_id`, `subject_ids`, `location`, `evidence_refs`, `severity`, `public_visibility`, `relationship_deltas`, `reputation_deltas`, `turning_point_candidate`.

#### [NEW] `src/core/models/reputation.py`
- `ReputationProfile` model: `defender_score`, `cowardice_score`, `greed_score`, `heroism_score`, `threat_notoriety`, `trustworthiness`, `reputation_tags` (list[str]).
- Bounded by [-10.0, 10.0] for each numeric dimension with Pydantic validators.

#### [MODIFY] `src/core/aspects/mind.py`
- Add `turning_points: list[TurningPointRecord]` to `NarrativeMemory` (capped at 20).
- Extend `BeliefRecord` with `knowledge_source: str` (default="direct"), `directness: float` (default=1.0), `source_confidence: float` (default=1.0).
- Extend `SocialBondPerception` with `loyalty`, `resentment`, `admiration`, `debt` fields.

#### [MODIFY] `src/core/models/social.py`
- Extend `SocialBond` with `loyalty`, `resentment`, `admiration`, `debt` fields.
- Extend `SocialRegistry.update_bond()` to accept new dimension deltas.

#### [MODIFY] `src/core/entities/entity.py`
- Add `reputation: ReputationProfile` field to Entity for public-facing state.

#### [MODIFY] `src/core/models/enums.py`
- Add `TurningPointKind` and `InterpretedLifeEventKind` enums.

---

## Stage 2 — Turning-Point Memory Salience & Pruning

### Objective
Add services that manage turning-point insertion, salience scoring, and pruning.

### Changes

#### [NEW] `src/core/logic/turning_points.py`
- `TurningPointService` class:
  - `calculate_salience(tp, current_tick, actor_motives, important_entity_ids) -> float`: Weighted salience from emotional_impact, motive relevance, entity importance, recency, severity.
  - `insert(entity, turning_point) -> bool`: Add a new TP, respecting cap (20). If at cap, prune lowest-salience entry. Returns whether insertion succeeded.
  - `prune(entity, current_tick) -> None`: Re-score all TPs, evict below threshold while preserving high-salience old entries.
  - `mark_resolved(entity, event_id) -> None`: Set `still_salient = False` for resolved events (e.g., revenge completed).

---

## Stage 3 — Event Interpretation Service

### Objective
Create the centralized translation layer that converts raw simulation data into `InterpretedLifeEvent`s.

### Changes

#### [NEW] `src/core/logic/event_interpreter.py`
- `EventInterpreterService` class:
  - `interpret_combat_aftermath(actor, defender, combat_result, world) -> list[InterpretedLifeEvent]`: Detects near_death, ally_died_nearby, avenged_ally, first_boss_encounter.
  - `interpret_flight(actor, threat_source, context) -> list[InterpretedLifeEvent]`: Detects fled_from_threat.
  - `interpret_position_hold(actor, threats_nearby, ticks_held, context) -> list[InterpretedLifeEvent]`: Detects held_position.
  - `interpret_looting(actor, danger_nearby, context) -> list[InterpretedLifeEvent]`: Detects looted_during_danger.
  - Private: `_assess_public_visibility(event, witnesses) -> float`: How visible was this event?
  - Private: `_calculate_severity(event) -> float`: How impactful is this event?

#### [MODIFY] `src/systems/gameplay/action_system.py`
- After authoritative combat result application (`CombatTraceUpdate` handling), invoke `EventInterpreterService.interpret_combat_aftermath()`.
- Route resulting `InterpretedLifeEvent`s into a new social-state application path.

---

## Stage 4 — Authoritative Social-State Application Pipeline

### Objective
Create a single centralized path for applying interpreted events into turning points, relationship deltas, reputation deltas, and motive adjustments.

### Changes

#### [NEW] `src/core/logic/social_state_applicator.py`
- `SocialStateApplicator` class:
  - `apply_interpreted_events(actor, events, world) -> list[IntentUpdate]`: For each event:
    1. If `turning_point_candidate` and salience threshold met → insert into turning points.
    2. Apply `relationship_deltas` via `SocialUpdate`s.
    3. Apply `reputation_deltas` to actor's reputation profile (respecting `public_visibility`).
    4. Adjust motive frustration/progress when relevant (e.g., near_death → frustrate `prove_strength`).
  - Returns typed `IntentUpdate` list for authoritative application.

#### [NEW] `src/core/logic/relationship_service.py`
- `RelationshipService` class:
  - `compute_relationship_deltas(event) -> dict[int, dict[str, float]]`: Maps event kinds to bond dimension changes.
  - `prune_relationships(entity, max_count) -> None`: Evict lowest-importance relationships when over capacity.
  - `compute_importance(bond, entity_motives) -> float`: Salience scoring for relationship prioritization.

#### [NEW] `src/core/logic/reputation_service.py`
- `ReputationService` class:
  - `compute_reputation_deltas(event) -> dict[str, float]`: Maps event kinds to reputation dimension changes.
  - `apply_reputation_delta(entity, deltas) -> None`: Bounded application with clamping.
  - Respects `public_visibility`: private acts do NOT become public reputation automatically.

#### [MODIFY] `src/systems/gameplay/action_system.py`
- Extend `_apply_updates` to handle new `ReputationUpdate` typed update.
- Wire `SocialStateApplicator` after event interpretation.

#### [NEW] `src/actions/base.py` — Add `ReputationUpdate(IntentUpdate)`
- `defender_delta`, `cowardice_delta`, `greed_delta`, `heroism_delta`, `threat_notoriety_delta`, `trustworthiness_delta`.

---

## Stage 5 — Social Knowledge Propagation

### Objective
Add bounded indirect knowledge transfer with source-confidence differentiation.

### Changes

#### [NEW] `src/core/logic/knowledge_propagation.py`
- `KnowledgePropagationService` class:
  - `propagate_threats(source, recipients, social_registry) -> list[PerceptionUpdate]`: Share dangerous actor identities with allies (trust > threshold).
  - `propagate_reputation(source, recipients, world) -> list[IntentUpdate]`: Share reputation knowledge with nearby allies.
  - All propagated beliefs marked with `knowledge_source="indirect"`, `directness=0.5`, `source_confidence=0.7`.

#### [MODIFY] `src/core/aspects/mind.py`
- `BeliefRecord` extensions already applied in Stage 1 become active here.
- Direct observation overwrites indirect knowledge.

#### [MODIFY] `src/ai/beliefs.py`
- `BeliefService.refresh_belief_from_observation()` sets `knowledge_source="direct"`, `directness=1.0`, `source_confidence=1.0` to overwrite indirect.
- `decay_stale_beliefs()` decays `source_confidence` for indirect beliefs faster.

---

## Stage 6 — Inspection and Life-Level Explanation

### Objective
Extend the chosen-entity inspection panel with relationship summaries, turning points, reputation, and life-change explanations.

### Changes

#### [MODIFY] `src/api/schemas.py`
- Add `TurningPointSchema`: `tick`, `kind`, `summary_tag`, `emotional_impact`, `involved_entity_ids`, `still_salient`.
- Add `RelationshipSummarySchema`: `target_id`, `target_name`, `trust`, `fear`, `loyalty`, `resentment`, `admiration`, `debt`, `rivalry`, `importance`.
- Add `ReputationSummarySchema`: `defender_score`, `cowardice_score`, `greed_score`, `heroism_score`, `threat_notoriety`, `trustworthiness`, `tags`.
- Add `LifeChangeExplanationSchema`: `turning_point_kind`, `affected_motive`, `affected_relationship_target_id`, `resulting_bias`, `tick`.
- Extend `EntityInspectionSchema` with `turning_points`, `relationships`, `reputation`, `life_changes`.

#### [MODIFY] Presenter modules
- Select top-5 turning points by salience, top-5 relationships by importance, compact reputation summary.
- Derive life-change explanations from recent turning points and their causal chains.

---

## Stage 7 — Testing and Validation

### Tests

#### [NEW] `tests/unit/ai/test_turning_points.py`
- Salient events create turning points.
- Low-value events do not.
- Cap and pruning rules work.
- Old but salient events survive pruning.

#### [NEW] `tests/unit/ai/test_event_interpreter.py`
- Combat aftermath → near_death, ally_died_nearby, avenged_ally events.
- Flight events → fled_from_threat.
- Position holding → held_position.
- Looting during danger → looted_during_danger.

#### [NEW] `tests/unit/ai/test_social_state_pipeline.py`
- Interpreted event → turning point + relationship delta + reputation delta end-to-end.
- Verify causality, not just field mutation.

#### [NEW] `tests/unit/ai/test_relationship_management.py`
- Bounded capacity and eviction.
- Top relationships surfaced correctly.
- Private events don't become public reputation.

#### [NEW] `tests/unit/ai/test_knowledge_propagation.py`
- Indirect knowledge weaker than direct.
- Direct observation overwrites indirect.
- Propagation only to trusted allies.

#### [MODIFY] `tests/unit/ai/test_social_integration.py`
- Extend with Phase 2 inspection contract tests.

---

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/unit/ai/test_turning_points.py -v
python -m pytest tests/unit/ai/test_event_interpreter.py -v
python -m pytest tests/unit/ai/test_social_state_pipeline.py -v
python -m pytest tests/unit/ai/test_relationship_management.py -v
python -m pytest tests/unit/ai/test_knowledge_propagation.py -v
python -m pytest tests/unit/ai/ -v --tb=short
python -m pytest tests/ -x --tb=short  # Full regression
```

### Manual Verification
- Run simulation for 100+ ticks and inspect entity panel for turning points, relationships, and reputation.
- Verify events produce different reputations for different behavioral archetypes.

---

## Non-Goals (Deferred)
- Daily/weekly routine simulation
- Household/home-role systems
- Inheritance/successor systems
- Regional/world consequence simulation
- Full rumor markets
- Natural-language storytelling generation
