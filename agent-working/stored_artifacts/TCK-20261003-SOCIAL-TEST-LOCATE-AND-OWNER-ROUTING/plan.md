---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING

Written at closure from what was done. The staging set was not created up front; the plan was reviewed as
the ticket text by test-architecture-reviewer on 2026-10-03, with the decisions below.

1. Select the social tests: `tests/unit/social` plus every file outside it that imports `src.systems.social_systems`.
2. Run them unchanged under coverage.py with `--source=src/systems/social_systems`, scratch coverage path, no repo artifacts.
3. Census their markers by collect-only with a read-only plugin.
4. Audit placement against `docs/testing/test_taxonomy.md` §5 and §8. Record, never move or mark.
5. Write section 2 of the shared report `docs/testing/social_test_report_2026-10-03.md`.
6. Update only the §3.1 Social / narrative row of `architecture_design_notes.md` (reviewer decision: no new
   table, no `regression_policy.md` change).

Scope guards: no test file touched; `party*.py`, `memory.py`, perception and dormant paths excluded from findings.
