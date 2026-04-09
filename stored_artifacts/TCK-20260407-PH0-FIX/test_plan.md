# Phase 0 Corrective Alignment Test Plan

## Existing Tests to Run:
- `tests/unit/logic/test_person_logic.py`: Verify personality and social bond motive biases.
- `tests/unit/logic/test_archetype_divergence.py`: Verify distinct motives for Slayer vs Defender.
- `tests/unit/logic/test_social_bonds.py`: Verify basic social bond math.

## New Tests to Add:

### 1. `tests/unit/logic/test_salience_pruning.py`
- Create memory log with mix of high impact (old) and low impact (recent) events.
- Apply `MemorySalienceService.prune`.
- Verify that a high-impact old event is preserved over a medium-impact old event.
- Verify weighted impact: `abs(impact) * (1 - decay * ticks_old)`.

### 2. `tests/integration/test_mutation_purity.py`
- Mock `Entity` and `Snapshot`.
- Call `AIBrain.decide()`.
- Compare `Snapshot` and `Entity` state before and after.
- Verify `entity.mind.narrative.memory_log` has not changed length.

### 3. `tests/unit/ui/test_inspector_curation.py`
- Mock an entity with specific traits and motives.
- Capture stdout of `EntityInspector.inspect_full`.
- Verify presence of personality labels (e.g. "Creative") and curated motive scores.

## Manual Verification:
- Launch CLI simulation.
- Pause and inspect multiple heroes.
- Verify "Likely Next Choices" aligns with current goal score logic.
