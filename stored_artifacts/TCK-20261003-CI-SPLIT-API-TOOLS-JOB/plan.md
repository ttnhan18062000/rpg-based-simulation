---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CI-SPLIT-API-TOOLS-JOB
artifact_type: plan
tags: [delivery, testing]
---

# Plan — TCK-20261003-CI-SPLIT-API-TOOLS-JOB

1. Measure equivalence first: collect-only IDs for the old job versus the union of the three new commands.
2. `.github/workflows/test.yml`: replace `api-tools` with `tools-a-e`, `tools-f-z` (single `Run` step each, own JUnit, upload, base-branch collection with the same ignore glob, Job summary) and `api-cli-engine` (per-directory steps, merge, upload, base collection, summary); update `slow.needs` and one comment. Install steps stay pip.
3. Update names and lists only in the three pinning tests; update the two tool docstrings and the planning docs that describe present behaviour.
4. New test file `tests/tools/test_ci_split_tools_jobs.py` pinning the split.
5. Verify locally; commit; after a real PR run, record the run link and the three job durations, then close.

## Scope guards
No `src/`, `.claude/`, `CLAUDE.md`, no change to which tests run or their markers, no moved test files, no new dependency, install step untouched, no assertion weakened.

## Acceptance-criteria map
| Criterion | Where |
|---|---|
| No `api-tools` job; three jobs; only historical mentions remain | step 2, 3; investigation 6 |
| ID sets equal | investigation 2 |
| Non-matching file runs | new test, scratch directory |
| Coverage gate and static tests pass | step 5 |
| Existing-test edits listed, names and lists only | ticket notes |
| `slow.needs` lists all three | step 2; new test |
| Green real PR run, three durations recorded | step 5, after push |
| No `src/`, `.claude/`, `CLAUDE.md` | step 5 |
