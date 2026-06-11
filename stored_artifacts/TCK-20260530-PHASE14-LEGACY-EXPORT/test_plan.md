---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE14-LEGACY-EXPORT
artifact_type: test_plan
tags: [phase14, legacy, export]
---

# Test Plan - Phase 14 Legacy Export

## Automated Verification Steps
1. Execute repository loading against the updated `data/content/` directory and ensure:
   - All exported items, recipes, enemies, regions, combat profiles, and cognition profiles load cleanly under standard pydantic models.
   - Run `pytest tests/unit/content/` to ensure zero compilation or loading regressions.
