---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-COG-PHASE3-DECISION
artifact_type: investigation
tags: [cog, phase3, decision]
---

# Investigation Report: Cognition Immediate Bugs

**Ticket ID:** TCK-20260527-COG-IMMEDIATE-BUGS  
**Date:** 2026-05-27  

---

## 1. Near-Death Panic Logic Bug (Task 6)
- **File:** `src/engine/cognition.py` ([cognition.py:L106-L109](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/cognition.py#L106-L109))
- **Logic:**
  ```python
  if hp_percent < 0.2:
      panic += 0.5
  elif hp_percent < 0.1:
      panic += 0.8
  ```
- **Finding:** Unreachable branch. Any value `< 0.1` is also `< 0.2`, so it matches the first `if` and never reaches the `elif`.
- **Solution:** Reverse the checks and add a `< 0.4` threshold for smoother scaling.

---

## 2. TownScorer Strategic Bridge Bug (Task 7)
- **File 1:** `src/ai/goals/scorers.py` ([scorers.py:L97](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/scorers.py#L97))
  - **Logic:** Returns `GoalScore(kind="town_return", utility=utility, target_pos=state.town_center)`. Target ID is defaulted to `None`.
- **File 2:** `src/systems/strategic_systems/intelligence.py` ([intelligence.py:L1171-L1173](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py#L1171-L1173))
  - **Logic:**
    ```python
    for g_score in modified_scores:
        if g_score.utility < 20.0 or g_score.target_id is None:
            continue
    ```
- **Finding:** Because `TownScorer` doesn't return `target_id`, it is always skipped by the strategic project loop.
- **Solution:**
  - Update `TownScorer` to return `target_id="town_center"`.
  - Update `StrategicIntelligenceSystem.evaluate_strategic_intent` to allow either `target_id` or `target_pos`.
