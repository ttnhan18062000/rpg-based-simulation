# Plan — TCK-20260619-E53Ca-CONFLICT-PHASE

## Steps

### Step 1: Create src/engine/military_conflict.py
- `MilitaryConflictPhase` class with `@staticmethod execute(state) -> StateUpdate`
- Reads `state.factions`, iterates lexicographic pairs, finds WAR pairs
- Logs `WAR_DETECTED` at DEBUG level per pair (internal observability only)
- Returns empty `StateUpdate()` (no mutations in E53Ca)
- No imports from src/domains/campaigns/

### Step 2: Wire into pipeline.py as Phase 8e
- Insert after Phase 8d (line ~213), before Phase 3 (adventure_decision)
- Follow exact t_start / run_phase / costs pattern of 8b–8d

### Step 3: Create tests/unit/faction/test_military_conflict_phase.py
- `test_military_conflict_phase_detects_war_pairs`: two factions with WAR relation → execute returns StateUpdate
- `test_military_conflict_phase_noop_on_peace`: no WAR pairs → returns empty StateUpdate
- `test_military_conflict_phase_noop_empty_factions`: empty factions → returns empty StateUpdate

## Scope Guards
- No mutations to RegionState, FactionState, territory — E53Cb+
- No SiegeState — E53Cb
- No territory transfer — E53Cc
- No military_strength drain — E53Cd
- Do NOT resolve owner_faction_id int/str mismatch — E53Cc

## Deviations
_None so far._
