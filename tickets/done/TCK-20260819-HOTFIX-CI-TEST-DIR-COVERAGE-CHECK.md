---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK
phase: done
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK

## Title
Add a static check that fails CI when a test directory isn't referenced in any test.yml job

## Status
DONE

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
- [x] The check fails when a directory with real `test_*.py` content (containing at least one
      non-`slow`/`extra_slow` test) is not covered by any fast-lane job's path list — verified by
      a fixture proving it catches a deliberately-introduced violation, not just that it passes
      today (per this repo's coverage-honesty convention, see
      `tests/tools/test_workflow_meta_conformance.py`'s own docstring). Proven three ways in
      `tests/tools/test_ci_workflow_test_coverage.py`: `test_fixture_catches_a_real_orphaned_fast_directory`
      (mixed fixture: covered / slow-only-legitimate / genuinely orphaned dirs in one run),
      `test_fixture_violation_is_resolved_once_the_directory_is_added_to_a_fastlane_job` and
      `test_fixture_loose_files_need_every_one_individually_listed_to_pass` (explicit
      before/FAIL -> after/PASS transitions, not just a passing case existing somewhere).
- [x] Running the check against the current repo state passes cleanly.
      `test_check_against_real_repo_state_passes_cleanly` passes — but only after this
      implementation also fixed a real, previously-undetected gap it found live (see
      Implementation Notes): `tests/unit/test_dirty_refresh.py`,
      `tests/unit/test_memory_probe.py`, `tests/unit/test_queue_worker_singleton.py` (3 files, 10
      tests, zero `slow`/`extra_slow` markers) sat directly under `tests/unit/` referenced by no
      job at all — same shape as the TCK-20260817 incident, just file- instead of
      directory-granularity. Per this repo's rule against editing a check to make it pass instead
      of fixing the underlying substance, `.github/workflows/test.yml` was fixed (each file added
      to the correct existing job's explicit path list), not the check weakened.
- [x] The check runs on every PR via an existing fast CI job.
      No `test.yml` wiring edit was needed: `tests/tools/test_ci_workflow_test_coverage.py` lives
      in `tests/tools/`, which `api-tools` (unconditional on every PR, no `if:` gate) already
      lists as a whole-directory path — the same job `test_workflow_meta_conformance.py` already
      runs under today. (The ticket's Scope text assumed this sibling ran via `arch-docs`; live
      verification of the current `test.yml` found it actually runs via `api-tools`'s
      `tests/tools` entry, not `arch-docs` — `arch-docs` has no `tests/tools` reference at all.
      The new file inherits the same real lane its sibling runs in, matching the intent of "wire
      it in alongside" without duplicating collection across two jobs.)
- [x] `docs/testing/content_migration_test_ownership.md` documents the new automated guard.
      Rule 7 (added by the prerequisite commit `92b6f02e`) was checked against the actual
      implementation and found already accurate as written — no edit was needed or made.

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

Context scan performed per project rule: `mcp__knowledge-search__search_docs` for "CI workflow
test directory coverage check orphaned test directories" (surfaced the TCK-20260817 incident
ticket and the TCK-20260819 sibling tickets referenced above), then read
`tests/tools/test_workflow_meta_conformance.py` and `tools/gate_checks/test_scope_coverage_static.py`
as the two closest real precedents before writing anything.

**Module** (`tools/gate_checks/ci_workflow_test_coverage.py`, new): follows
`test_scope_coverage_static.py`'s shape (pure mapping/predicate functions feeding one aggregator,
no CLI/argparse entry point, consumed only via pytest import). Key functions:
- `parse_job_pytest_paths(text)` — line-based (not regex-over-multiline, deliberately, after an
  earlier catastrophic-backtracking regex attempt during investigation took minutes to
  finish on the real 300+ line workflow file) parser: workflow text -> `{job_name: {path_token}}`.
  Strips `--ignore=` tokens before collection so an excluded path is never miscounted as covered.
  Represents the `slow` job's blanket `pytest tests/` as the single token `"tests"`.
- `directories_from_test_files(paths)` — groups a flat file list by immediate (non-recursive)
  parent directory.
- `is_directory_covered(dir, fastlane_paths)` — directory-vs-directory match, direct or
  ancestor-path.
- `directory_is_covered_by_file_listings(files, fastlane_paths)` — **added mid-implementation,
  not in the original plan sketch**: needed once the real-repo run surfaced `tests/unit/` itself
  as a directory with 3 loose files, none in a themed subdirectory, each listed individually by
  *file* path (not directory path) in the fix below. Directory-level matching alone couldn't
  recognize this as covered; this function checks that every file directly in the directory is
  itself an explicit path token somewhere in the fast-lane set.
- `file_is_fully_slow_marked(path)` / `directory_is_slow_only_legitimate(files, root)` — AST-based
  (module `pytestmark`, function decorator, or `Test*` class decorator) check that every
  `test_*` function in a file/directory is `slow`/`extra_slow`-marked, so the `slow` job's blanket
  scan is legitimate sufficient coverage for it (resolves the ticket's stated Open Question:
  confirmed `tests/regression/` is the only such directory in the real repo today —
  `test_check_against_real_repo_state_recognizes_regression_as_slow_only_legitimate` pins this).
- `check_ci_workflow_test_coverage(workflow_path, repo_root, test_files=None)` — aggregator;
  `test_files` is injectable so fixture tests exercise it against a synthetic `tests/` tree in
  `tmp_path` without a real git repo (default shells out to `git ls-files -- 'tests/*test_*.py'`).

**Real gap found and fixed (deviation from a literal reading of Scope, required by the
"don't edit a check to make it pass instead of fixing the substance" hard rule):** running the
check against the real, current `.github/workflows/test.yml` before making any workflow edits
showed exactly one genuine, previously-unknown orphan beyond the already-known
`tests/regression/` case: `tests/unit/` directly contains three loose test files
(`test_dirty_refresh.py`, `test_memory_probe.py`, `test_queue_worker_singleton.py` — 10 test
functions total, verified via `grep` to carry zero `slow`/`extra_slow` markers and to be
unreferenced anywhere in `.github/workflows/` or `Makefile`) that no job referenced at all — same
failure shape as the 16-directory incident this ticket exists to prevent recurrence of, just
file-granularity instead of directory-granularity, and never previously caught because the `slow`
job's `-m "slow or extra_slow"` filter silently excludes unmarked tests even though they're
textually inside its blanket `pytest tests/` scan. Fixed by adding
`tests/unit/test_dirty_refresh.py` to `unit-core-world`'s explicit path list (core-state theme,
matches `AuthoritativeState`/`DirtySet` under test) and `tests/unit/test_memory_probe.py` +
`tests/unit/test_queue_worker_singleton.py` to `unit-infra`'s (observability/queue theme). A short
comment referencing this ticket ID was added above `unit-core-world`, matching this file's
existing per-fix comment convention (`TCK-20260817-...`, `TCK-20260818-...` comments already
present). This is a completeness fix to the existing job lists (adding path entries), not a
job-splitting-structure change, so it stays inside the ticket's Out of Scope boundary.

**CI wiring (Scope item 2):** the ticket's Scope text assumed `test_workflow_meta_conformance.py`
(the sibling this ticket's check follows) runs via the `arch-docs` job. Verifying the real,
current `test.yml` (as instructed, given the sibling nesting ticket had just changed this file in
the same session) found this assumption factually wrong: `arch-docs` has no `tests/tools`
reference anywhere; `test_workflow_meta_conformance.py` actually runs today via `api-tools`'s
`tests/tools` whole-directory entry (unconditional on every PR, no `if:` gate). Since the new
check file was placed in `tests/tools/` (per Scope item 1's own instruction to follow that
sibling's pattern), it inherits the same real `api-tools` lane automatically — no `test.yml` edit
was needed or made for wiring; adding a second, redundant `tests/tools` listing to `arch-docs`
would only duplicate collection of the whole directory across two jobs for no benefit.

**Doc rule (Scope item 3):** `docs/testing/content_migration_test_ownership.md` rule 7 (added by
prerequisite commit `92b6f02e`, already naming this ticket ID in past tense) was re-read against
the actual implementation as instructed. Its wording is accurate as written — no edit made.

## Test Summary
- `.venv/bin/python3 -m pytest tests/tools/test_ci_workflow_test_coverage.py -v --tb=short` — 27
  passed (new file; includes real-repo end-to-end checks, unit tests for every pure function, and
  three coverage-honesty fixture tests with explicit before/FAIL -> after/PASS transitions).
- `.venv/bin/python3 -m pytest tests/tools tests/architecture -m "not slow and not extra_slow" --tb=short -q`
  — 2433 passed, 12 skipped, 31 deselected, 1 xfailed, 0 failed (broader regression surface;
  confirms nothing else broke).
- `.venv/bin/python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` —
  confirmed `.github/workflows/test.yml` is still valid YAML after edits, all 13 jobs intact.
- `graphify update .` run after the `tests/`/`tools/` changes per project convention.

## Files Changed
- `tools/gate_checks/ci_workflow_test_coverage.py` (new) — the static check module.
- `tests/tools/test_ci_workflow_test_coverage.py` (new) — pytest suite for the module, including
  the required coverage-honesty fixtures.
- `.github/workflows/test.yml` (modified) — fixed the real orphan gap found live (3 files added
  to `unit-core-world` and `unit-infra`'s explicit path lists, plus an explanatory comment); no
  wiring edit needed for the new test file itself (already covered via `api-tools`'s existing
  `tests/tools` entry).
- `tickets/inprogress/TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK.md` (this file) — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary.
- `docs/testing/content_migration_test_ownership.md` — read and verified, not modified (rule 7
  already accurate).

## Completion Summary
Added `tools/gate_checks/ci_workflow_test_coverage.py` and
`tests/tools/test_ci_workflow_test_coverage.py`: a static, git-ls-files-driven check that every
`tests/` directory containing a `test_*.py` file is referenced by at least one fast-lane CI job's
explicit `pytest` path list (directly, as a descendant of a listed parent, or — for loose files
with no themed subdirectory — individually by file path), unless every test in it is legitimately
`slow`/`extra_slow`-marked and thus correctly covered only by the `slow` job's blanket scan. The
check runs on every PR automatically via `api-tools`'s existing `tests/tools` entry (same lane its
`test_workflow_meta_conformance.py` sibling already runs in — no new wiring needed). Running it
against the real, current repo surfaced one genuine previously-undetected gap (3 loose,
unmarked test files directly under `tests/unit/`, 10 tests, never run in CI by any job) which was
fixed in `.github/workflows/test.yml` rather than used to weaken the check, so the check now
passes cleanly against real repo state for a real reason. `docs/testing/content_migration_test_ownership.md`
rule 7 was verified accurate and left unchanged.
