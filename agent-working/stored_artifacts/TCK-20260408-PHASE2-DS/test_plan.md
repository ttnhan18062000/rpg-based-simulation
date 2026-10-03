---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260408-PHASE2-DS
artifact_type: test_plan
tags: [phase2, ds]
---

# Test Plan — Phase 2 Design Shift

## Existing Tests to Run (Regression)
```bash
python -m pytest tests/unit/ai/ -v --tb=short
python -m pytest tests/unit/core/ -v --tb=short
python -m pytest tests/unit/mind/ -v --tb=short
python -m pytest tests/ -x --tb=short
```

## New Tests

### 1. Turning Point Tests (`tests/unit/ai/test_turning_points.py`)
| Scenario | Expected |
|---|---|
| High-impact interpreted event → turning point created | TP appears in `entity.mind.narrative.turning_points` |
| Low-value routine event → no turning point | TP list unchanged |
| Cap at 20 → oldest low-salience evicted | List stays at ≤ 20, high-salience preserved |
| Old but defining event → survives pruning | Event with kind=NEAR_DEATH and high emotional_impact retained |
| `mark_resolved` → still_salient=False | Resolved TP has still_salient=False |

### 2. Event Interpreter Tests (`tests/unit/ai/test_event_interpreter.py`)
| Scenario | Expected |
|---|---|
| Combat: entity HP < 20% → near_death | `InterpretedLifeEvent(kind=NEAR_DEATH)` emitted |
| Combat: allied entity killed in radius → ally_died_nearby | Event with correct subject_ids |
| Combat: killed entity who killed ally → avenged_ally | Event referencing the revenge chain |
| Entity flees from threat → fled_from_threat | Event with severity proportional to threat |
| Entity holds position 5+ ticks near threats → held_position | Event with ticks_held in evidence |
| Entity loots while enemies in vision → looted_during_danger | Event with public_visibility > 0 |

### 3. Social State Pipeline Tests (`tests/unit/ai/test_social_state_pipeline.py`)
| Scenario | Expected |
|---|---|
| ally_died_nearby → fear+resentment delta on killer + turning point + cowardice_score on fleer | Full causal chain verified |
| avenged_ally → admiration/heroism deltas | Relationship and reputation updates |
| fled_from_threat → cowardice_score up if public | Only if public_visibility > threshold |
| private act → no reputation change | Reputation unchanged when public_visibility == 0 |

### 4. Relationship Management Tests (`tests/unit/ai/test_relationship_management.py`)
| Scenario | Expected |
|---|---|
| 25 bonds created (max_bonds=20) → 5 lowest evicted | Only 20 remain, highest importance preserved |
| Top-5 relationships by importance → correct selection | Selection matches highest-importance bonds |
| Private event → no public reputation | ReputationProfile unchanged |
| Indirect knowledge → lower confidence | source_confidence < 1.0 |

### 5. Knowledge Propagation Tests (`tests/unit/ai/test_knowledge_propagation.py`)
| Scenario | Expected |
|---|---|
| Threat shared to trusted ally → belief created | Indirect belief with source_confidence=0.7 |
| No sharing to untrusted entity → no belief | Entity memory unchanged |
| Direct observation overwrites indirect → higher confidence | source_confidence=1.0, directness=1.0 |
| Stale indirect decays faster | Confidence drops below direct-belief decay rate |

### 6. Inspection Contract Tests (extend `tests/unit/ai/test_social_integration.py`)
| Scenario | Expected |
|---|---|
| Inspection includes turning_points | Non-empty list for entity with TPs |
| Inspection includes relationships | Top-N relationships present |
| Inspection includes reputation | ReputationSummary present |
| Inspection includes life_changes | At least one LifeChangeExplanation |
| Outputs are bounded | No full dumps — max 5 TPs, 5 relationships |

## Edge Cases
- Entity with no combat history → empty turning points, empty relationships (valid)
- Entity killed before any interpreted events → no crash, graceful empty state
- Two entities fighting each other → both get correct reciprocal relationship updates
- Boss entity → deterministic personality still generates meaningful turning points
