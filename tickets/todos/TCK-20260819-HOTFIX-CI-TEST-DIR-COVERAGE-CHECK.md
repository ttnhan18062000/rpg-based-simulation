---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK
phase: open
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK

## Title
Add a static check that fails CI when a test directory isn't referenced in any test.yml job

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`.github/workflows/test.yml` enumerates every test directory by explicit path in each job's
`pytest` invocation — there is no glob or auto-discovery. This already caused a real incident:
`TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS` found 16 directories (83 files, 439 tests,
all added by one commit) that no job ever referenced — 439 of 440 tests had never run in CI at
all, caught only by a manual "is anything missing from the workflow?" audit, not by any automated
guard. That ticket fixed the specific 16 directories; it added no lasting check against
recurrence. Live re-verification this session found the exact same exposure still exists today:
`tests/regression/test_behavioral_5k.py` is not referenced by path in any job — it currently only
runs because it happens to carry `@pytest.mark.extra_slow`, which the `slow` job's blanket
`pytest tests/` scan incidentally catches. That's marker-luck, not a guarantee; a new "fast"
(non-marked) test directory added today would silently never run, exactly like the 16 before it.

## Scope
- Add a static test (e.g. `tests/tools/test_ci_workflow_test_coverage.py`, following the existing
  `tests/tools/test_workflow_meta_conformance.py` pattern of parsing a real workflow/config file
  and asserting structural properties about it) that:
  1. Parses `.github/workflows/test.yml`'s job `run:` blocks for `pytest <paths...>` invocations
     and collects every `tests/...` path token referenced across all jobs (including the `slow`
     job's blanket `pytest tests/`).
  2. Walks the real `tests/` tree via `git ls-files` (not raw filesystem — avoids local
     `__pycache__` noise) to find every directory containing at least one `test_*.py` file.
  3. For each such directory, confirms it is covered by at least one **fast-lane** job's explicit
     path list (directly, or as a descendant of a listed parent path) — the `slow` job's blanket
     scan only legitimately covers `slow`/`extra_slow`-marked tests, so it must not be treated as
     sufficient coverage for a directory that also contains unmarked (fast) tests.
  4. Fails with a message naming the exact orphaned directory/directories if any gap is found.
- Wire the new test into an existing fast CI job (`arch-docs`, alongside
  `test_workflow_meta_conformance.py`) so it runs on every PR.
- Add a rule to `docs/testing/content_migration_test_ownership.md`'s "New Suite Creation Rules"
  documenting that this is now automatically enforced — while still requiring rule 3 (explicitly
  add the new path to the correct job) to be followed by hand, since the check only catches
  omissions after the fact and doesn't choose which job/lane a new directory belongs in.

## Out of Scope
- Any change to the job-splitting structure itself (core/world vs. gameplay vs. infra lanes) —
  this ticket only guards completeness of the existing structure, not its shape.
- Making the `slow` job's blanket scan authoritative for fast-lane coverage — that would mask
  exactly the gap this ticket exists to catch.

## Acceptance Criteria
- [ ] The check fails when a directory with real `test_*.py` content (containing at least one
      non-`slow`/`extra_slow` test) is not covered by any fast-lane job's path list — verified by
      a fixture proving it catches a deliberately-introduced violation, not just that it passes
      today (per this repo's coverage-honesty convention, see
      `tests/tools/test_workflow_meta_conformance.py`'s own docstring).
- [ ] Running the check against the current repo state passes cleanly.
- [ ] The check runs on every PR via an existing fast CI job.
- [ ] `docs/testing/content_migration_test_ownership.md` documents the new automated guard.

## Related Tickets
- TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS (the incident this ticket prevents from
  recurring — fixed the symptom, not the lasting cause)
- TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING (sibling ticket; this check should pass cleanly
  against that ticket's post-move `test.yml`, since the domains-nesting move keeps the moved
  content covered via the existing `tests/unit/domains` parent-path entry)
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (recent, unrelated CI hygiene work on the same file —
  cross-reference only, no scope overlap)

## Related Docs
- .github/workflows/test.yml
- docs/testing/content_migration_test_ownership.md
- tests/tools/test_workflow_meta_conformance.py (the pattern this ticket's check follows)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- .github/workflows/test.yml
- tests/tools/ (new check file)

## Assumptions / Open Questions
- Exact handling of directories covered *only* by the `slow` job (all their tests are
  `slow`/`extra_slow`-marked) needs a decision at implementation time: treat as covered (correct
  today) or still require an explicit fast-lane-adjacent listing for discoverability. Leaning
  toward "covered is correct" since that's the current `tests/regression/` case and it's not
  actually broken — but confirm no other all-slow directory exists that would silently pass this
  check while still being awkward to discover.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
