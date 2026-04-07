# Test Plan: TCK-20260407-PHASE1-DS

## Existing Tests to Run
- `pytest tests/unit/ai/`: Ensure basic AI loops don't break.
- `pytest tests/unit/core/aspects/`: Ensure Mind aspect serializes.

## New Tests to Add

### 1. Personality Divergence
- **File**: `tests/unit/ai/test_personality_divergence.py`
- **Scenario**: Two same-class heroes (e.g., Rangers) in same position with same HP, but one is `aggressive: 0.9, caution: 0.1` and other is `aggressive: 0.1, caution: 0.9`.
- **Assertion**: Aggressive ranger chooses HUNT/ATTACK, Cautious ranger chooses FLEE/WANDER.

### 2. Belief vs Truth
- **File**: `tests/unit/ai/test_belief_based_decisions.py`
- **Scenario**: Entity observes a high-threat enemy, then enemy goes into fog/out of sight and heals.
- **Assertion**: Entity still "believes" enemy is high-threat until next observation or enough staleness decay occurs.

### 3. Motive Influence
- **File**: `tests/unit/ai/test_motive_influence.py`
- **Scenario**: Entity has `build_wealth` motive vs `seek_safety` motive.
- **Assertion**: Wealth seeker prioritizes LOOT even with moderate threat; Safety seeker prioritizes FLEE.

### 4. Inspection Schema
- **File**: `tests/api/test_behavioral_inspection.py`
- **Assertion**: API payload for entity inspection contains `personality`, `motives`, and `beliefs` sub-sections.
