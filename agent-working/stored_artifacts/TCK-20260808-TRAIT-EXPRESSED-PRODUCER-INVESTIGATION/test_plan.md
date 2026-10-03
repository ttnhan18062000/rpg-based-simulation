---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION
artifact_type: test_plan
tags: [progression, simulation-quality]
---

# Test Plan — TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION

Investigation concluded no real producer exists (a genuine "unimplemented mechanic" finding, not
a bug to fix) — no code change lands, so no new tests are needed. Verification here means
confirming the "zero real producer" claim itself is accurate, not assumed:

## Normal flow
- `grep -rn "traits_add=\|breakthroughs_add=" src/ --include=*.py` returns zero matches outside
  the field declarations — re-run as the literal verification step, not just cited from memory.

## Edge cases
- Confirm the 3 real test-file construction sites (`test_breakthroughs.py`,
  `test_event_shapers_progression.py`, `test_domain_6_hardening.py`) are genuinely test-only, not
  accidentally reachable from any production import path.

## Failure modes
- N/A — no code changed.

## Regression-prone paths
- N/A — no code changed; existing tests for the apply-path (`test_domain_6_hardening.py`,
  `test_breakthroughs.py`) already pass and are unaffected.

## Scoped test commands
- `pytest tests/unit/progression/test_breakthroughs.py tests/unit/core/test_domain_6_hardening.py
  tests/unit/observability/test_event_shapers_progression.py -q` (confirm untouched, still green)
