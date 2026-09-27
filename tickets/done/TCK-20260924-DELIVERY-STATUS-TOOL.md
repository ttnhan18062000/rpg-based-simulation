---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-STATUS-TOOL
phase: done
date: 2026-09-24
tags: [delivery, ai, process-improvement]
---

# TCK-20260924-DELIVERY-STATUS-TOOL

## Title
One tool call returns a typed PR delivery verdict, with the CI triage tree encoded — replacing the
~14 polling round-trips per PR

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Measured over W30–W39 (`agent-monitoring/data/2026-W3*/tools.jsonl`, 116,168 Bash calls, read from
`origin/main` at `75ab942b4`): **1,796 `gh` invocations against 106 `gh pr create` = 16.9 `gh`
calls per PR, of which ~86% is pure observation** — `gh pr view` 408, `gh api repos/…` 398,
`gh pr checks` 348, `gh run view` 202, `gh run list` 124, `gh pr diff` 35. That is roughly 14
polling round-trips per PR, each one a round-trip in a very large context, because no tool answers
"what is the state of this PR?" in a single call. Full figures: plan §1.1.

Worse, the *reasoning* applied to those polls lives only in `CLAUDE.md` prose, and four separate
incidents are currently defended only by an agent remembering a paragraph:

- **An absent run is not a failing run.** A `pull_request:`-triggered workflow cannot produce a run
  at all while the PR is `CONFLICTING`, because GitHub cannot compute `refs/pull/N/merge`. This
  presents identically to a slow queue. (`TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`)
- **A TLS block can read as "0 pending" and look green.** ([[project_ci_poll_tls_block_false_green]])
- **Step-level conclusions survive a log block** — they are metadata, never subject to the
  Fortiguard block on log hosts, and can localize a failure with zero log access.
- **A partial log fetch is not evidence that log fetching works** — the block is per-job-blob-shard,
  so a multi-job fetch can silently omit exactly the job that failed.

Plan §3.7 calls these "the highest-value automation targets in the whole epic": known, reproduced,
and currently un-encoded. This ticket builds `tools/delivery/pr_status.py`.

## Scope
1. **`tools/delivery/pr_status.py`** — new module and package directory (neither exists today).
   Takes a PR number, or infers it from the current branch. Returns a typed verdict:

   | verdict | meaning |
   |---|---|
   | `GREEN` | every required check completed successfully **against the current head SHA** |
   | `PENDING` | runs exist and are in progress, established by a **positive** in-progress signal |
   | `FAILING` | at least one completed check failed, with job and step conclusions attached |
   | `ABSENT` | no run exists for this SHA, **plus the reason** |
   | `UNKNOWN` | state could not be established — never reported as green |

2. **Head-SHA binding.** Every verdict names the SHA it was computed against. A verdict for a stale
   SHA is `UNKNOWN`, not `GREEN` — a run that passed on the previous commit says nothing about the
   current one ([[feedback_no_monitoring_commits_while_polling_ci]] is the sibling trap).

3. **The `ABSENT` reason branch.** When `gh api repos/{owner}/{repo}/actions/runs?head_sha=<sha>`
   returns `total_count: 0`, distinguish the causes rather than reporting a bare absence:
   - PR `mergeable` is `CONFLICTING` **and** the workflow's `on:` block is `pull_request:`-only for
     this branch → fully explained; the fix is to resolve the conflict. The output must say so, and
     must say that a re-trigger commit, force-push or branch recreation will not help.
   - the push may never have landed → compare `git ls-remote origin <branch>` against the PR's own
     `headRefOid` and report which it was.

4. **`UNKNOWN` as a first-class verdict, not an error.** When a log or API fetch fails in a way that
   cannot be distinguished from "nothing to report" — notably the TLS block on
   `results-receiver.actions.githubusercontent.com` / `*.blob.core.windows.net` — the verdict is
   `UNKNOWN` with the reason attached. Detect the block by subject/issuer rather than retrying:
   a cert reading as a network filter block page is not an SSL problem to fix.

5. **Step-level conclusions always included on `FAILING`.** Fetch
   `gh api repos/{owner}/{repo}/actions/jobs/{job_id} --jq '.steps[]'` — name + `conclusion` per
   step. This is metadata, never log content, so it survives the TLS block and is often enough to
   localize the failure alone.

6. **`--json` output** alongside the human-readable form, matching the `MARKER:`-prefixed JSON CLI
   contract the `tools/gate_checks/` scripts already use, so a caller can consume it directly.

## Out of Scope
- **Polling loops.** This tool answers "what is the state now" once and exits. It must not sleep,
  retry on a timer, or watch — a caller decides when to ask again.
- **Producing any commit or write while running.** A status tool that commits re-triggers the CI it
  is measuring ([[feedback_no_monitoring_commits_while_polling_ci]]). Read-only, no exceptions.
- **Classifying *why* a check failed** into own-regression / flake / baseline-drift / environment.
  That is `TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER` (plan M5), which consumes this tool's output.
- **Fixing anything, re-running a job, or re-triggering a workflow.** Reporting only.
- **Merging, or advising whether to merge.** Merge is the user's call.
- **Any blocking behavior.** Exit code reflects "did the tool run", never "is the PR green" — a
  `FAILING` verdict still exits zero. A non-zero exit means the tool itself broke.

## Acceptance Criteria
1. For a PR with all checks passed against the current head SHA, one invocation returns `GREEN` and
   names the SHA.
2. For a PR whose latest run is against an **older** SHA than the current head, the verdict is
   `UNKNOWN` (or `PENDING` if a run for the current SHA is genuinely in progress) — **never**
   `GREEN`. Proven by a test with a fixture where run SHA ≠ head SHA.
3. For a `CONFLICTING` PR with a `pull_request:`-only trigger and `total_count: 0`, the verdict is
   `ABSENT` and the output states the conflict as the cause and names conflict resolution as the
   fix. Proven by a fixture test.
4. When the run list cannot be fetched, the verdict is `UNKNOWN` — **asserted directly by a test
   that simulates a failed/blocked fetch and asserts the verdict is not `GREEN`.** Assert on the
   blocked path, not only on the happy path; this is the exact shape of the incident being encoded.
5. A `FAILING` verdict includes per-step name and conclusion for each failing job, obtained without
   fetching any log body.
6. `--json` emits a single parseable object containing verdict, head SHA, and reason.
7. The tool performs **no** write: a test asserts the working tree and git index are unchanged
   after a run.
8. Exit code is zero for every verdict including `FAILING` and `UNKNOWN`; non-zero only on internal
   error. Asserted by test.
9. A scoped `pytest tests/tools/` (or the correct directory for this module) run passes, and the
   command plus result is recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` — the absent-run incident this encodes; read it
  before implementing, it has the verified `total_count: 0` reproduction
- `TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER` — downstream consumer (plan M5)
- `TCK-20260924-DELIVERY-COST-MEASUREMENT` — measures whether this ticket actually reduced `gh` calls

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §3.7 — the verdict set and the
  four incidents, authoritative; §1.1 — the cost evidence
- `CLAUDE.md` `### CI Failure Triage` (lines 399–417) — the prose decision tree being encoded. Do
  **not** edit it in this ticket; `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` owns that edit.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/delivery/` — **new directory**, created by this ticket
- `tools/gate_checks/` — 23 existing scripts sharing the `MARKER:`-prefixed JSON CLI contract to
  mirror; `monitoring_anomaly_validator.py` and `done_checker_static.py` are the closest shapes
- `.github/workflows/test.yml` — the `on:` block this tool reads to explain an `ABSENT` run
  (`pull_request:` with no branch filter, `push:` restricted to `branches: [main]`)

## Assumptions / Open Questions
1. **Whether to parse `gh` CLI output or call `gh api` directly.** The `ABSENT` branch already
   requires `gh api .../actions/runs?head_sha=` and `gh pr view --json mergeable`, so the API is
   likely the more uniform surface. Note `gh pr checks` has **no `--json` flag in this
   environment** — a known constraint, so it is a poor primary source.
2. **What counts as "required".** If no checks are marked required on the repo, `GREEN` should mean
   "every check that ran, completed successfully" — state whichever definition is implemented, in
   the module docstring.
3. Whether `deploy-docs.yml` runs should count toward a PR's verdict or be reported separately.
   Recommend separately: a docs-publish failure is not a code regression.
4. Whether a fixture-based test suite is enough, or one live smoke test against a real PR is needed.
   Prefer fixtures — a live test is non-deterministic and would break the testing rule.

## Implementation Notes
**This is the highest-value ticket in the epic and it runs first** (see `SEQUENCE.md`). It depends
on nothing, and `TCK-20260924-DELIVERY-COST-MEASUREMENT` needs it landed to have a real before/after
to measure.

The four incidents in §3.7 are not hypotheticals — each cost real time and each is already written
down as prose in `CLAUDE.md`. The point of this ticket is that prose defended by memory becomes a
verdict defended by a test. Where an incident's rule is subtle, encode the rule *and* cite the
ticket or memory it came from in a comment, so a future reader can tell a deliberate branch from an
accident.

The `UNKNOWN`-is-never-green requirement is the single most important line in the ticket. The
failure it prevents already happened: a poll loop read a TLS error as "0 pending" and reported CI
green while it was still running.

## Test Summary
- `python3 -m pytest tests/tools/test_delivery_pr_status.py -v` (run via the repo's own venv,
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` — bare `python3` lacks
  `pydantic` in this sandbox, unrelated to this ticket): **28 passed**. One test per Acceptance
  Criterion plus edge cases/failure modes per `staging_artifacts/TCK-20260924-DELIVERY-STATUS-TOOL/
  test_plan.md`, including AC2's stale-SHA-yields-UNKNOWN fixture, AC3's CONFLICTING+trigger-only
  ABSENT fixture, AC4's two failed-fetch variants (non-zero exit; exit-0-but-unparseable-stdout),
  AC5's no-log-fetch assertion, AC7's working-tree-unchanged assertion, and AC8's exit-code
  parametrization across all five verdicts.
- Full regression check: `python3 -m pytest tests/tools/ -m "not slow"` — **2933 passed, 25
  skipped, 28 deselected, 1 xfailed**, 0 failed. No existing test broke from adding
  `tools/delivery/__init__.py` or the new test file.

## Files Changed
- `tools/delivery/__init__.py` (new) — package marker, empty.
- `tools/delivery/pr_status.py` (new) — the status-verdict module and CLI per this ticket's Scope.
- `tests/tools/test_delivery_pr_status.py` (new) — 28 tests, one per Acceptance Criterion plus
  edge/failure-mode coverage.
- `staging_artifacts/TCK-20260924-DELIVERY-STATUS-TOOL/{investigation,plan,test_plan}.md` (new).

## Completion Summary
Built `tools/delivery/pr_status.py`, a single-call typed PR delivery verdict
(`GREEN`/`PENDING`/`FAILING`/`ABSENT`/`UNKNOWN`) encoding the CLAUDE.md CI Failure Triage decision
tree as tested code. All I/O routes through an injectable `run_command` callable, so every branch —
including the two real incidents this ticket exists to encode (a `CONFLICTING` PR producing zero
runs, and a blocked/failed fetch being misread as an empty/green result) — is covered by a
deterministic fixture test rather than a live network call. Head-SHA binding is enforced
client-side (every returned run is re-checked against the expected head SHA before being trusted),
which is what makes the `ABSENT` (confirmed zero runs, known cause) vs `UNKNOWN` (only a stale run
found, or the fetch itself failed) distinction in AC2/AC3 both correct and testable. No polling
loop, no write of any kind, and the CLI always exits 0 except on a genuine internal error in the
tool's own code (AC8) — verified directly by test, not just by design intent.

No known gaps at close. Followed CLAUDE.md's `## Related Docs` instruction not to touch
`CLAUDE.md` itself in this ticket (that edit belongs to
`TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`).
