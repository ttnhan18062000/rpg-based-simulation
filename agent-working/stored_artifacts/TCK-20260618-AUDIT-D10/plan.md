---
ticket_id: TCK-20260618-AUDIT-D10-TESTS
type: plan
date: 2026-06-18
---

# D10 Plan

## Approach
Structural assessment only — no coverage% instrumentation.
Run unit+integration suite, classify failures by root cause cluster, score each cluster
by regression risk using a 3-dimension rubric.

## Scoring Rubric (proposed)
3 dimensions × 5 = 15 max (Regression Risk):
- Failure Breadth: how many tests are affected / cascade scope
- Domain Criticality: how core to engine correctness
- Masking Risk: can the failure pass silently or be hidden by test ordering

## Steps
1. [done] Run test suite, collect counts
2. [done] Classify failures by root cause
3. [done] Identify well-covered and coverage-gap domains
4. [todo] Write D10 audit document
5. [todo] Update audit_dimensions.md
6. [todo] Move ticket to done, append working log, write monitoring entries
