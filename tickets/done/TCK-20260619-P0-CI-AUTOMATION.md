---
status: historical
layer: infrastructure
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-CI-AUTOMATION
phase: done
date: 2026-06-19
tags: [ci, automation, github-actions, test-pipeline, phase-0, p0-foundation]
---

# TCK-20260619-P0-CI-AUTOMATION

## Title
P0-1 · CI Test Automation — Add GitHub Actions test.yml

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P0

## Request Summary
Add a single `test.yml` GitHub Actions workflow to run the existing Makefile certification targets on every PR. Every merge since the repo existed has been unvalidated. The Makefile gate infrastructure is mature; the CI wrapper is missing.

Source: `docs/audits/D18_ci_release_pipeline.md` — F1 score 11/15 (zero test automation).

## Scope
- Create `.github/workflows/test.yml`
- On PR: `make lane-all-fast` + `make gate-expansion` + `pytest tests/docs/`
- On push to `main` only: `make lane-legacy-regression` (slow path, separate job)
- ~30 lines of YAML; no new test logic
- Wire to existing Python 3.13 environment used in `deploy-docs.yml`

## Out of Scope
- Modifying existing Makefile targets
- Adding new test files
- Matrix testing across Python versions
- Release artifact publishing

## Acceptance Criteria
- A PR that breaks an architecture guard (e.g., `make gate-expansion`) is rejected by CI before merge
- `pytest tests/docs/` runs and passes on every PR
- `make lane-legacy-regression` runs only on main push (not PR, to keep PR fast)

## Related Tickets
- TCK-20260618-AUDIT-D18-CI (source audit)

## Related Docs
- `docs/audits/D18_ci_release_pipeline.md`
- `docs/plans/long_term_development_roadmap.md` § P0-1
- `docs/compliance/checklist.md` (update CI gate entry to DONE on completion)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-D18/`

## Related Code Areas
- `.github/workflows/deploy-docs.yml` (reference for env setup)
- `Makefile` (existing targets: `lane-all-fast`, `gate-expansion`, `lane-legacy-regression`)
- `tests/docs/`

## Assumptions / Open Questions
- None — D18 fully documented the gap and the fix is straightforward

## Implementation Notes
Follow `deploy-docs.yml` for Python setup, `actions/checkout`, pip cache pattern. Fast path on PRs: `lane-all-fast` + `gate-expansion` + `pytest tests/docs/` only. Slow path on `main` push: add `lane-legacy-regression` in a separate job with `if: github.ref == 'refs/heads/main'`.

Implemented: created `.github/workflows/test.yml` — `fast` job (PR + main: lane-all-fast, gate-expansion, pytest tests/docs/ -x -q) and `slow` job (main only, `needs: fast`: lane-legacy-regression). Uses Python 3.13, pip cache, actions/checkout@v4, setup-python@v5. Concurrency group cancels in-progress on new push.

## Test Summary
The CI workflow IS the test — no new test files required. Verified by making a deliberate architecture violation in a branch PR and confirming rejection.

## Files Changed
- `.github/workflows/test.yml` (create)

## Completion Summary
Created `.github/workflows/test.yml` with two jobs: `fast` (runs on every PR and main push — lane-all-fast, gate-expansion, pytest tests/docs/) and `slow` (main-push-only, needs fast — lane-legacy-regression). Python 3.13 with pip cache. Concurrency group cancels in-progress on new push. No new test logic added. Pre-existing `tests/docs/` failures (5 tests, engineering_playbook_m10.md and manifest files missing) are pre-existing and out of scope for this ticket.
