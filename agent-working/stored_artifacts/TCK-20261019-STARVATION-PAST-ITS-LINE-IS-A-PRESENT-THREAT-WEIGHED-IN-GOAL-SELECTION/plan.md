---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION
tags: []
---

# plan - TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION

## Plan
1. scorers.py: `_hunger_escalated_unless_threatened` (keeps the escalated pull at hunger >= STARVING_LINE), used by EatScorer and `_hunger_without_open_way`.
2. Tests, docs (Bible 04 section 1, parity STRAT-284, divergence entry).
3. Measure vs step one (rpg-v3-held-panic a49896e1c results in v3proof): crowded_frontier stop line first.
Scope guard: sleep gate and tactical order untouched.
