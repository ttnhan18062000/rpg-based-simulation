---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-DELIVERY-STATUS-TOOL
date: 2026-09-24
tags: [delivery, ai]
---

# Investigation — TCK-20260924-DELIVERY-STATUS-TOOL

## Confirmed facts

- `tools/delivery/` does not exist yet — new package directory, no prior module to conflict with.
- `.github/workflows/test.yml`'s `on:` block (read directly): `pull_request:` with **no** branch
  filter, `push: branches: [main]`, plus `schedule:` and `workflow_dispatch:`. A feature branch's
  own commits get CI **only** via the `pull_request` event, evaluated against `refs/pull/N/merge` —
  a ref GitHub cannot compute while the PR is `CONFLICTING`. Matches
  `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`'s verified claim exactly (read that closed
  ticket in full before starting — see `## Implementation Notes` there for the same direct
  verification).
- `gh pr checks` has **no `--json` flag in this environment** (per the ticket's own Assumption 1) —
  confirmed by CLAUDE.md's own CI Failure Triage prose citing the same constraint. `gh api` is the
  uniform surface for both the runs list and the `ABSENT` branch's `mergeable` check, so the module
  uses `gh api`/`gh pr view --json` throughout, never `gh pr checks`.
- `gh api repos/{owner}/{repo}/...` accepts the **literal** placeholder strings `{owner}` and
  `{repo}` and substitutes them from the current git repo context — this is a real `gh` CLI feature,
  not something this tool needs to resolve itself by calling `gh repo view`.
- Two existing `tools/gate_checks/*.py` shapes were read in full to mirror conventions:
  - `monitoring_anomaly_validator.py` — `List[dict]` of `{"status": "PASS"|"FAIL", "evidence": "..."}`,
    `MARKER:` + `json.dumps(...)` stdout contract, **non-zero exit on FAIL**. This ticket's own
    Out-of-Scope explicitly requires the *opposite* exit-code contract (zero on every verdict
    including `FAILING`/`UNKNOWN`, non-zero only on internal error) — so the `MARKER:` JSON-stdout
    convention is reused, but the exit-code rule is not; this divergence is deliberate and stated in
    the module docstring so a future reader doesn't "fix" it back to gate-check parity.
  - `done_checker_static.py` — real `argparse` CLI (`--ticket-id`, `--part`, etc.), human-readable
    `[label] condition: STATUS — evidence` lines plus a final `RESULT:` summary line. This ticket's
    `--json` alongside human-readable output (AC6) mirrors this dual-mode shape.
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` (read in full): confirms the exact `mergeable`
  + trigger-block check and the `git ls-remote` vs `headRefOid` disambiguator this ticket's Scope
  item 3 asks for — the CLAUDE.md prose this ticket's tool is meant to encode as a real verdict.

## Design decisions made during investigation

1. **Head-SHA binding is enforced client-side, not only via the API query param.** `gh api
   .../actions/runs?head_sha=<sha>` already filters server-side, but the module additionally
   filters every returned run against the expected head SHA in Python before treating it as
   "applicable". This is what makes AC2's stale-SHA fixture test meaningful and deterministic at
   the unit level, independent of whatever the mocked transport returns.
2. **`ABSENT` vs `UNKNOWN` split, resolving an apparent tension between AC2 and AC3.** AC3
   (`total_count: 0`, `CONFLICTING`, `pull_request:`-only) is `ABSENT` — we positively confirmed
   zero runs exist and have a specific, documented cause. AC2 (a run exists, but only for an older
   SHA than current head) is `UNKNOWN`, not `ABSENT` — a stale run's existence isn't informative
   about *why* the current SHA has no run yet, so there is no confirmed cause to report as
   `ABSENT`'s "plus the reason" requires. Decision: `ABSENT` is reserved for the two enumerated,
   explained-absence branches in ticket Scope item 3 (CONFLICTING+trigger-only, or push-not-landed);
   every other "no applicable run" shape — including "only stale runs found" — is `UNKNOWN`.
3. **`UNKNOWN` on fetch failure is a return-code check, not a content-shape guess.** The real
   incident this ticket encodes (`[[project_ci_poll_tls_block_false_green]]`) is a TLS error being
   *misread* as an empty/zero result. The fix implemented here is structural: every `gh`/`git`
   subprocess call is inspected for a non-zero return code (or unparseable stdout where JSON is
   expected) **before** its stdout is ever treated as "the answer" — a failed fetch can never fall
   through to an empty-list code path. No `openssl`/certificate-inspection step is implemented in
   the tool itself (out of scope — that is a human/CLAUDE.md diagnostic technique for *log* fetches,
   which this tool never performs); a stderr keyword scan (`certificate`, `ssl`, `tls`, `x509`,
   `fortinet`, `fortiguard`) is used only to make the reported reason more specific when available,
   never to decide the verdict.
4. **Job/step conclusions fetched exactly as the ticket specifies (Scope item 5), not via the
   combined `.../actions/runs/{id}/jobs` payload's own embedded `steps` array.** The ticket names
   `gh api repos/{owner}/{repo}/actions/jobs/{job_id}` (singular, per-job) as the source of step
   conclusions. The module calls the jobs-list endpoint first to find which jobs failed, then the
   per-job endpoint for each failing job's steps — matching the ticket's literal command and keeping
   the log-body/metadata distinction explicit at the call-site level.
5. **Workflow trigger parsing is generic, not hardcoded to `main`.** `on.push.branches` is parsed
   from the actual `.github/workflows/test.yml` YAML (via PyYAML, already a repo dependency — see
   `tools/parity_ledger_writer.py` for prior use) rather than hardcoding `"main"`, so a future change
   to the trigger block doesn't silently desync this tool from CLAUDE.md's own documented condition.

## Assumptions carried into the plan

- Per ticket Assumption 4: fixtures only, no live smoke test against a real PR (non-deterministic,
  violates the Testing Rule's determinism requirement).
- Per ticket Assumption 3: `deploy-docs.yml` runs are not merged into this PR's verdict — this tool
  only ever reasons about the workflow file the caller points it at (defaulting to `test.yml`), so
  the exclusion is structural, not a special case.
- Per ticket Assumption 2: "required" is defined as "every check that ran, completed successfully" —
  no repo-configured required-checks list is read. Stated in the module docstring per the ticket's
  own instruction.
