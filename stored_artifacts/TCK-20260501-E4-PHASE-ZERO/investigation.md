# E4 Phase 0 — Investigation Log

## Coverage Gap Analysis
- **Claimed**: 35.22% (580 items)
- **Verified**: 8.41% (80 items)
- **Gap**: 27.81% (500 items checked but without machine-readable trace)

## Root Causes of Trace Failures
1. **ID Disconnect**: Many items use a descriptive name in the checklist (e.g., `strategic_state_persistence`) while the code uses a class name or different tag (e.g., `StrategicComponent`).
2. **Missing Markers**: Logic is implemented (e.g., `AttributePoints` in `Progression`) but lacks the `VERIFIED v2` tag.
3. **Legacy Residue**: Some items are marked `[x]` but refer to logic that was either moved, renamed, or is currently only partially implemented in V2.

## Key Subsystems for Reconciliation
### 1. Strategic Mind
- Current markers in `src/systems/strategic.py` and `src/strategy/` need to be mapped to checklist IDs.
- Verified: `strategic_state_persistence`, `project_objective_continuity`, `strategic_blocker_inference`.

### 2. Social / Contracts
- `SocialAppraisalSystem` and `ContractService` contain implementation for betrayal, trust, and recruitment, but markers are inconsistently named.

### 3. Combat Matrix
- `LegalityServiceV2` contains many verified markers, but some (like `flanking_geometric`) are missing from the checklist's `[x]` set.

## Next Steps
- Standardize the checklist to use IDs that match current source markers.
- Rename source markers where the checklist ID is more descriptive of the "RPG Law".
