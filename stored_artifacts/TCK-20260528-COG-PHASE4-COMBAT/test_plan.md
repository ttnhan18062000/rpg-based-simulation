---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-COG-PHASE4-COMBAT
artifact_type: test_plan
tags: [cog, phase4, combat]
---

# Test Plan: Phase 4 — Combat Engagement Cognition

This document outlines the detailed verification plan for Phase 4.

## Automated Tests

We will build the complete suite of 13 test files to verify:
1. **Unit-Level Integrity**: Isolated test files for perception estimates, self estimates, risk evaluation, selector enums, and intent mappings.
2. **Integration Phase Filtering**: Ensure skipping of stunned/dead heroes and locked strategic project entities works as intended.
3. **Integrated Scenarios**:
   - Brave and cautious entities select divergent postures.
   - Unknown equal opponents WATCH or PROBE instead of instantly engaging.
   - Lost combat updates generalized and specific memory, causing future avoidance or calling help.
   - Monster self-preservation causes a badly wounded monster to retreat.
4. **Performance Gate Budgets**: Benchmark 100+ entities to verify they consume less than 5ms warm-up/clean updates.
