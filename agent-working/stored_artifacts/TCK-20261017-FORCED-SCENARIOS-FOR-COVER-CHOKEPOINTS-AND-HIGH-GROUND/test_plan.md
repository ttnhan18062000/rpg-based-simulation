---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND
artifact_type: test_plan
tags: []
---

# test_plan - TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND

- The 6 new tests, controls included.

## Proof Plan
- Level: kernel-level scenario tests.
- Proof kind: behavioural, each with a control arm and a switched-off scratch mutation that must fail.
- Oracle source: owner ruling 2026-10-17 via rpg-planner; divergences 2.129 and 2.130.
- Expected effect: none on gate-world digests (test-only).
- Selected commands: `python -m pytest tests/unit/combat -q`.
