---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260417-COMBAT-MOVEMENT-FINALIZE
artifact_type: investigation
tags: [combat, movement, finalize]
---

# Investigation: Milestone 7 Diagnostic Failures

## Current Failures

### 1. Documentation Integrity (`test_observability_reasons_exist_in_code`)
- **Issue**: The test fails because it doesn't scan `src/core/models/reason_codes.py` where the canonical reason strings are defined.
- **Root Cause**: `ActionReason.reason_text` is the source of truth, but the test only checks logic files.

### 2. Rollout Boundaries (`test_rollout_movement_v2_vs_v1`, etc.)
- **Issue**: `MovementModel` and `TacticalEvaluator` return `ActionReason` objects, but tests perform substring checks using `in` on the reason field.
- **Root Cause**: Without `__str__` defined on `ActionReason`, `in` doesn't find the expected strings. Additionally, some strings in the tests (e.g., "Legacy") are slightly different from the actual output (e.g., "Legacy Fallback").

### 3. ActionSystem Rejection Prefix
- **Issue**: `ActionSystem` only adds "REJECTED: " if the reason is a string. If it's an `ActionReason`, it stays as an object.
- **Root Cause**: Discrepancy between v1 (string-based) and v2 (object-based) observability.

## Approach
- Define `__str__` and `__contains__` (or just ensure `.reason_text` is checked) to bridge the gap.
- Align all test strings with `reason_codes.py`.
