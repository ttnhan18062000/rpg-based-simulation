---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Title
M4f: After the two-week soak, make the code-health ratchet, SARIF step and mypy baseline block new violations

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Decision 8.5/8.10: advisory for a two-week soak, then blocking for new violations only. Owner decision 2026-10-03: mypy flips together with the ratchet; jscpd stays report-only. BLOCKED until the soak end date, which TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB records here.

## Scope
- Soak review first: list false positives and baseline-sync events seen during the soak, the reviewed-row count, and **how many mypy-baseline syncs were needed** (and how often the code-health registry needed a reseed); propose fixes for any false-positive class before flipping
- Remove `continue-on-error` from the `code-health` job (ratchet excluding jscpd), the SARIF step if separate, and the typecheck job's `mypy` step (the gate `tools.code_health.mypy_gate` already returns 1 on new errors and 2 if it cannot run); remove `|| true` from the `make typecheck-py` recipe
- Ask the owner to mark the checks required in GitHub branch protection (owner action; record it)
- Update INFRA-TYPE-001 text, the CI comment, environment guide and tests that pin advisory status

## Out of Scope
- Any file under src/
- Gating jscpd or line-count beyond what the ratchet already does (jscpd report-only)
- Raising strictness or tightening ceilings

## Acceptance Criteria
- [ ] Soak review written with dates, counts and dispositions
- [ ] The three gates fail a PR that introduces a new violation and pass one that does not (demonstrated on real PR runs)
- [ ] Owner confirmed the required-check setting
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
- TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
- TCK-20261003-MYPY-BASELINE-ADVISORY

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/parity_ledger/infrastructure.yaml (INFRA-TYPE-001)

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tests/static/test_typecheck_gate_configured.py

## Assumptions / Open Questions
- Soak start: date of batch PR merge (the PR that carries the advisory CI job; the closure commit of TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB writes the real date). Soak end: start + 14 days
- Blocking gates affect every domain that edits src/; announce the date to other planners before flipping

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
