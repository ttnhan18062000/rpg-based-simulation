---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE13-SCHEMA-EXPANSION
artifact_type: test_plan
tags: [phase13, schema, expansion]
---

# Test Plan - Phase 13 Schema Expansion

## Automated Verification Steps
1. Add new test file `tests/unit/content/test_runtime_catalog.py` containing tests:
   - Validating loading of mock items, recipes, enemies, and regions.
   - Validating that validator catches dangled references (e.g. recipe referencing non-existent ingredient item).
