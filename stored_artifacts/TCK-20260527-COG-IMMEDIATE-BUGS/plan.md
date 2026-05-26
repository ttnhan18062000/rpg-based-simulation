# Technical Implementation Plan: Cognition Immediate Bugs

## Goal Description
Resolve two high-priority bugs in `AppraisalSystem` (unreachable `< 0.1` HP check branch) and `TownScorer` + strategic project loop (missing target ID and filtering logic) that prevent correct panic retreats and town-return strategic behavior.

---

## Proposed Changes

### Component 1: Cognition & Emotional Appraisal

#### [MODIFY] [cognition.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/cognition.py)
Modify `evaluate_emotional_state` to reverse the HP checking order and add the `< 0.4` intermediate threshold to ensure panic levels scale monotonically with low health:
- Check `hp_percent < 0.1` first, adding `0.8` to panic.
- Check `hp_percent < 0.2` second, adding `0.5` to panic.
- Check `hp_percent < 0.4` third, adding `0.2` to panic.

---

### Component 2: Town Scorer & Strategic Intent

#### [MODIFY] [scorers.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/scorers.py)
Modify `TownScorer.score` to return a non-None canonical target ID `town_center`.

#### [MODIFY] [intelligence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py)
- Modify the strategic goal-scoring loop to support position-only target matching safely by skipping only if both `target_id` and `target_pos` are `None`.
- Fix the `NameError` inside `resolve_blockers` where `candidate_ids` was not defined.
