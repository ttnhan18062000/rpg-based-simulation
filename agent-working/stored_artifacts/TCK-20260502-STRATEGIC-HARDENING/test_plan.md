---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260502-STRATEGIC-HARDENING
artifact_type: test_plan
tags: [strategic, hardening]
---

# Test Plan: Strategic Hardening E5.5

## Scenarios

### 1. Strategic Bandwidth (194, 195, 196)
- Setup: Entity with `max_leads=2`.
- Action: Generate 5 leads in one tick.
- Expectation: Only 2 leads are accepted; 3 are rejected with `INSUFFICIENT_CAPACITY`.

### 2. Interaction Interruption (159)
- Setup: Entity channeling harvest.
- Action: Apply 10 damage (assuming 100 HP max).
- Expectation: Interaction is reset; `progress` returns to 0.

### 3. Group Priority (197)
- Setup: Group with Leader and Member. Leader attacks Target A. Member has personal project targeting Target B.
- Action: Run tactical decision.
- Expectation: Member switches to Target A to support Leader.

### 4. Tick Budget (120)
- Setup: Profile with `max_tick_budget_ms=10`.
- Action: Inject slow worker logic.
- Expectation: Kernel aborts and reports `BUDGET_EXHAUSTED`.
