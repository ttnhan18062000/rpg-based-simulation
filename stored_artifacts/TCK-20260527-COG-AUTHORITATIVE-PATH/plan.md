# Implementation Plan: TCK-20260527-COG-AUTHORITATIVE-PATH

## Goal
Establish clean, single authoritative strategic planning and document bounds clearly.

## Proposed Changes
1. **Add Documentation Comments**: Add explicit block comments to:
   - `src/engine/domain/cognition.py`
   - `src/engine/tactical.py`
   - `src/systems/strategic_systems/intelligence.py`
   detailing the exact flow and split between strategic planning (authoritative pipeline pass), emotional appraisal, tactical decision, and action execution.

2. **Add Verification Tests**:
   - `test_single_strategic_update_per_tick` proving each entity receives exactly one strategic update per strategic tick.
   - `test_tactical_consumes_selected_strategic_state` proving tactical decisions read the active project state.
