---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D18-CI
phase: open
date: 2026-06-18
tags: [audit, ci, release-pipeline, certification, github-actions]
---

# TCK-20260618-AUDIT-D18-CI

## Title
D18 — CI / Release Pipeline Completeness Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit the automated CI and release pipeline for completeness. Identify what is gated
automatically vs. what requires manual invocation before a release.

## Scope
- Survey all GitHub Actions workflows
- Map Makefile test/release targets to CI coverage
- Check release-readiness conditions against actual enforcement
- Assess certification harness CI integration

## Out of Scope
- Fixing CI gaps
- Performance benchmarking

## Acceptance Criteria
- docs/audits/D18_ci_release_pipeline.md written with scoring rubric
- audit_dimensions.md D18 row updated to done
- Working log and monitoring entries written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)
- TCK-20260618-AUDIT-D10-TESTS (121 test failures are invisible to CI)

## Related Stored Artifacts
- staging_artifacts/TCK-20260618-AUDIT-D18/

## Implementation Notes
Key finding: only one CI workflow exists (deploy-docs.yml — docs deploy only).
No test CI workflow. All test targets (make test, lane-*, certification) are local-only.
Release-readiness conditions in project_lawbook.md are manual.

## Test Summary
N/A

## Files Changed
- docs/audits/D18_ci_release_pipeline.md (create)
- docs/audits/audit_dimensions.md (update)
- tickets/working_log.csv (append)
- agent-monitoring/runs.jsonl + events.jsonl (append)

## Completion Summary
D18 audit complete. Central finding: one CI workflow exists (`deploy-docs.yml`, docs-only); zero test automation.
All Makefile gates are local-only. 3 release-readiness conditions from project_lawbook.md are manually enforced.
Certification harness (10+ test files) is never run by CI. P0 follow-up: add `test.yml`.
5 findings scored: F1=11/15, F2=10/15, F3=7/15, F4=5/15, F5=5/15.
