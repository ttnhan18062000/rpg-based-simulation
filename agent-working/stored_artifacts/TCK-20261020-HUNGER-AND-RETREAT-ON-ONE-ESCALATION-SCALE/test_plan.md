---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
tags: []
---

# test_plan - TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A)

New file `tests/unit/ai/test_retreat_escalates_in_its_consequence_band.py`, built on the row 83 test's real frontier_living_world s42 scene (merchant 37, hunter 45):
1. **Acceptance:** at hunger 95 and 100, hp in the full band (hp 1/85, bravery 0, hunter adjacent), CombatRetreatScorer outscores EatScorer.
2. With no hostile perceived (hunter moved beyond 10 tiles), the retreat utility equals the raw formula, and EatScorer wins at hunger 100.
3. Band edges: no escalation at hp >= 0.4, full +60 at hp <= 0.15, monotone between (with a hostile present).
4. `retreat_pull` unit cases in `tests/unit/engine/test_need_pull.py` (onset, full, midpoint 30).
5. A brave subject at the onset edge (bravery near 1, hp 0.39) still loses to hunger 100: "strong enough" is the appraised threat (panic and the hp band), not any threat.
6. Replace the row 83 pin `test_the_starving_pull_exceeds_the_retreat_ceiling...` with a pin of the new ceiling (raw 150 + 60 = 210). Needs the planner's yes.

Regression runs: `tests/unit/ai/`, `tests/unit/strategic/test_expanded_goals.py`, `tests/unit/engine/test_need_pull.py`, `tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py` (expected to be at risk: the merchant's hunger now loses to retreat at the goal level while the hunter is in view). Then `-m "not slow"` over `tests/unit/ai tests/unit/engine tests/unit/strategic`.
