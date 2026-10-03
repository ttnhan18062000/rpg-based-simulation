---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-GAP
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260915-SIDECAR-ATTRIBUTION-GAP

| AC | Covered by |
|---|---|
| Classify legitimate vs. lost | investigation.md's direct sampling/per-tool/per-session breakdown (narrative evidence, not a unit test — this is corpus classification, not code behavior) |
| Disposition recorded | plan.md + ticket Completion Summary |
| Spend sections state coverage | `test_generate_retro.py` extension: coverage key present + rendered |
| Detector ratchets, no zero assertion | `test_sidecar_attribution_coverage_check.py`'s floor-pin (may only increase, mirroring the ceiling-may-only-decrease convention in the opposite direction) |

## Regression coverage

- `tests/tools/test_generate_retro.py` full file, plus the new coverage tests.
- `tests/tools/test_sidecar_attribution_coverage_check.py` (new).
- `make sidecar-attribution-coverage-check` confirmed against the real corpus.
