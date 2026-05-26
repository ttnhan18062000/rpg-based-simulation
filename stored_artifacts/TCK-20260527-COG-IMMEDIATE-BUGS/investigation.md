# Investigation Report: Cognition Immediate Bugs

**Ticket ID:** TCK-20260527-COG-IMMEDIATE-BUGS

---

## 1. Near-Death Panic Logic Bug (Task 6)
- **File:** `src/engine/cognition.py`
- **Finding:** Unreachable branch. Any value `< 0.1` is also `< 0.2`, so it matches the first `if` and never reaches the `elif`.
- **Solution:** Reverse the checks and add a `< 0.4` threshold for smoother scaling.

---

## 2. TownScorer Strategic Bridge Bug (Task 7)
- **File 1:** `src/ai/goals/scorers.py`
- **File 2:** `src/systems/strategic_systems/intelligence.py`
- **Finding:** Because `TownScorer` doesn't return `target_id`, it is always skipped by the strategic project loop which checks `g_score.target_id is None`.
- **Solution:**
  - Update `TownScorer` to return `target_id="town_center"`.
  - Update `StrategicIntelligenceSystem.evaluate_strategic_intent` to allow either `target_id` or `target_pos` (skip only if both are `None`).

---

## 3. resolve_blockers NameError Bug
- **Finding:** Pre-existing `NameError` in `resolve_blockers` in `src/systems/strategic_systems/intelligence.py` due to missing `candidate_ids`.
- **Solution:** Defined `candidate_ids = list(state.entities.keys())`.
