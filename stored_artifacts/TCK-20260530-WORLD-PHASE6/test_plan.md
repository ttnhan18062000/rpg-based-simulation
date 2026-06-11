---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE6
artifact_type: test_plan
tags: [world, phase6]
---

# Test Plan: Context-Aware Validation System (Phase 6)

## Scenarios to Cover

1. **Context Filtering**:
   - Verify that rules execute or are skipped depending on the context passed to the validator.
   - For example, `NoResourcesWarningRule` must be skipped in the `MODULE` validation context.

2. **Severity Overrides**:
   - Verify that rules can dynamically escalate or de-escalate issue severities based on the context.

3. **Strict Validation**:
   - Verify that strict mode honors context boundaries. E.g., warnings in `MODULE` context shouldn't crash if they are not error-level in that context.

4. **Multi-layer Assembly Validation Report**:
   - Verify that the resolver successfully runs catalog, module, composition, assembly, and world validation, producing a highly structured validation report in the resolved bundle.

## Execution

We will run:
```bash
.venv/bin/pytest tests/unit/worldbuilding/test_world_validator.py -v
```
and also add tests in a new/updated unit test module for Phase 6.
