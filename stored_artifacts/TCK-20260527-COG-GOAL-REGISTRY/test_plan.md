# Test Plan - TCK-20260527-COG-GOAL-REGISTRY

We will verify that the new goal scorers and personality-based biases function correctly and deterministically.

## Scenarios to Test

### 1. Unit Tests for New Scorers
- **`CombatEngageScorer`**:
  - No hostiles -> utility is 0.0.
  - Hostile present -> utility scales with bravery and stamina. Returns hostile ID and position.
- **`CombatRetreatScorer`**:
  - Full HP, no panic -> utility is 0.0.
  - Low HP or high panic -> utility is high, reduced by bravery. Returns town center.
- **`RecoverScorer`**:
  - High HP and stamina -> utility is 0.0 or very low.
  - Low HP or low stamina -> utility increases based on missing resources. Returns nearest inn or town center.
- **`ResolveBlockerScorer`**:
  - No blockers -> utility is 0.0.
  - Unresolved blocker -> utility is high (e.g. 80.0). Returns target detail.

### 2. Personality-Difference Verification
- Setup two entities: one Brave (bravery = 1.0) and one Coward (bravery = -1.0 or 0.0).
- Expose both to a threat.
- Assert Brave entity has a higher utility for `combat_engage` than Coward entity.
- Assert Coward entity has a higher utility for `combat_retreat` than Brave entity.

### 3. Deterministic Tie-Breaking
- Setup a scenario where two different goal scorers return the exact same utility score (e.g. 50.0).
- Run scoring multiple times.
- Assert the chosen candidate is completely stable and sorted deterministically (e.g., alphabetically by goal kind when utility is tied).

### 4. Integration Tests
- Run one full strategic tick.
- Assert high utility goal kind becomes the active project.
