---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-DELIVERY-STATUS-TOOL
date: 2026-09-24
tags: [delivery, ai]
---

# Plan — TCK-20260924-DELIVERY-STATUS-TOOL

## Module: `tools/delivery/pr_status.py` (+ `tools/delivery/__init__.py`)

### Public shape

```python
def compute_pr_status(
    pr: str | None = None,
    branch: str | None = None,
    workflow_path: Path = Path(".github/workflows/test.yml"),
    run_command: Callable[[list[str]], CommandResult] = default_run_command,
) -> dict:
    """Returns {"verdict", "head_sha", "reason", "failing_jobs"}."""
```

All I/O goes through the injected `run_command` callable — `(returncode, stdout, stderr)` per call —
so every branch is unit-testable without a network call or a real `gh`/`git` binary.

### Decision tree (mirrors CLAUDE.md's CI Failure Triage + plan §3.7, now as code not prose)

1. Resolve PR info: `gh pr view [<pr>] --json number,headRefOid,mergeable,baseRefName`.
   - Command fails → `UNKNOWN`, `head_sha: null`, reason names the failed command.
2. `head_sha = pr_info["headRefOid"]`.
3. Fetch runs: `gh api repos/{owner}/{repo}/actions/runs?head_sha=<head_sha>`.
   - Command fails or stdout doesn't parse as JSON → `UNKNOWN` (never treated as `total_count: 0`).
     Reason includes a TLS/cert keyword hint when stderr matches one, else the raw failure.
4. Filter `workflow_runs` client-side to `run["head_sha"] == head_sha` → `applicable_runs`.
5. `applicable_runs` non-empty:
   - Any applicable run `status == "completed"` and `conclusion == "failure"` → `FAILING`. For each
     such run, fetch `.../actions/runs/{run_id}/jobs`, filter jobs to `conclusion == "failure"`, and
     for each failing job fetch `.../actions/jobs/{job_id}` for `.steps[]` (name + conclusion). Any
     of these fetches failing degrades that one job's detail to `"steps": []` with a note, not the
     whole verdict to `UNKNOWN` — a partial job-detail fetch failure is not the same incident as the
     top-level runs-list fetch failing.
   - Else all applicable runs `conclusion == "success"` → `GREEN`.
   - Else any applicable run `status` in `{"in_progress", "queued", "waiting", "requested",
     "pending"}` → `PENDING`.
   - Else → `UNKNOWN` (unrecognized status/conclusion combination — never silently GREEN).
6. `applicable_runs` empty, but `workflow_runs` (unfiltered) is non-empty → `UNKNOWN`: a stale run
   exists for an older SHA; nothing establishes current-SHA state. This is AC2's fixture shape.
7. `applicable_runs` empty and `workflow_runs` is empty (genuine `total_count: 0`) → determine
   `ABSENT` reason:
   a. `git ls-remote origin <branch>` (branch from `pr_info["headRefName"]` if not passed explicitly)
      vs `head_sha`. Mismatch → `ABSENT`, reason: push may not have landed, states both SHAs.
      `ls-remote` itself failing → do **not** silently fall through to (b); treat as `UNKNOWN`
      (the disambiguator itself is unavailable, so we cannot rule out "push didn't land").
   b. Else, `pr_info["mergeable"] == "CONFLICTING"` and `workflow_covers_branch_via_push(...)` is
      `False` for this branch → `ABSENT`, reason states the CONFLICTING+trigger-only cause and
      explicitly states that a re-trigger commit / force-push / branch recreation will not help
      (AC3, and Scope item 3's explicit output requirement).
   c. Else → `ABSENT`, reason: no matching run and no known cause identified (honest fallback; still
      `ABSENT` because zero-count was positively confirmed, distinguishing it from step 6's `UNKNOWN`).

### `workflow_covers_branch_via_push(workflow_path, branch) -> bool`
Parses the workflow YAML's `on.push.branches` list via PyYAML. No `push` key, or `push` present with
no `branches` key → covers every branch (`True`). `branches` present → exact membership only (glob
patterns out of scope, no such pattern exists in this repo's own `test.yml` today).

### CLI (`argparse`, mirrors `done_checker_static.py`'s dual-mode shape)
```
python3 tools/delivery/pr_status.py [--pr N] [--branch BRANCH] [--workflow-path PATH] [--json]
```
- Default (no `--json`): human-readable line(s) — verdict, head SHA, reason, and one line per
  failing job/step if `FAILING`.
- `--json`: single `json.dumps({...})` object to stdout, matching AC6 (verdict, head SHA, reason —
  plus `failing_jobs` since it's part of the same payload and dropping it would make `--json`
  strictly less informative than the human-readable mode).
- Exit code: **always 0** except an uncaught internal error in the tool's own code (AC8) — the
  verdict computation itself never raises for a `gh`/`git` failure, since every failure path above
  resolves to a returned `UNKNOWN` verdict, not an exception.

## Tests: `tests/tools/test_delivery_pr_status.py`

One test per Acceptance Criterion, fixture-driven via a fake `run_command` (a small dict-keyed or
sequential stub matching on the command's first few argv tokens), plus the module-level unit tests
implied by the design decisions:

1. AC1 — all applicable runs `success` against current head SHA → `GREEN`, SHA named.
2. AC2 — fixture: `workflow_runs` contains one run whose `head_sha` differs from `pr_info`'s
   `headRefOid` → `UNKNOWN`, never `GREEN`. A second variant: same stale run present, but a second
   run *does* match current head SHA and is `in_progress` → `PENDING` (the parenthetical case).
3. AC3 — fixture: runs fetch returns `total_count: 0`, `pr_info["mergeable"] == "CONFLICTING"`,
   `workflow_covers_branch_via_push` returns `False` for the branch → `ABSENT`, reason names the
   conflict and states resolving it (not re-triggering) is the fix.
4. AC4 — fixture: the runs-fetch `run_command` call returns a non-zero returncode (simulating the
   TLS block) → `UNKNOWN`, asserted directly, not inferred from an empty list. A second variant
   returns exit 0 but unparseable stdout — same assertion, covering the "looked like success but
   wasn't JSON" shape.
5. AC5 — fixture: one applicable run `FAILING` with two jobs, one `conclusion: failure` — assert the
   returned `failing_jobs` payload has job name + per-step name/conclusion, and assert the fake
   `run_command` was never called with any log-fetching endpoint (i.e., only the jobs-list and
   per-job endpoints appear in the recorded call log — no `/logs` path anywhere).
6. AC6 — `--json` CLI invocation (via `subprocess` against the real script with a monkeypatched
   `PR_STATUS_TEST_FIXTURE` env var, or by calling `main()` directly with an injected fixture
   loader) emits one `json.loads`-able object containing `verdict`, `head_sha`, `reason`.
7. AC7 — snapshot `git status --short` / `git rev-parse` output (or, simpler and fully hermetic: a
   fixture-only unit test asserting `compute_pr_status` never calls `run_command` with a `git`
   subcommand other than `ls-remote`, and never calls `gh` with `pr create`/`pr merge`/any mutating
   verb) plus one integration-style test that runs the module against a real fixture in a temp repo
   copy and diffs `git status --short` before/after.
8. AC8 — every fixture combination above (`GREEN`/`PENDING`/`FAILING`/`ABSENT`/`UNKNOWN`) asserts
   the CLI's exit code is `0`; a separate test forces an uncaught exception (e.g. malformed
   `run_command` return shape) and asserts a non-zero exit only there.
9. AC9 — record the actual `pytest tests/tools/test_delivery_pr_status.py` command and result in the
   ticket's `## Test Summary` once run.

## Out-of-scope guardrails carried into the implementation
- No `while`/`sleep`/retry loop anywhere in `pr_status.py` — one call in, one verdict out.
- No write of any kind (no `git commit`, no file write beyond stdout) — enforced by AC7's test.
- No classification of *why* FAILING beyond job/step conclusions (that's M5, out of scope here).
- No merge advice, no exit-code-as-blocking-signal (AC8).
