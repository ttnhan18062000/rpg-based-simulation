---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW
phase: done
date: 2026-10-19
tags: [platform, delivery, security]
---

# TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW

## Title
CI: .github/workflows/security-scan.yml — gitleaks (secrets) on every PR and Semgrep (static) path-gated, both report-only, plus the roles diff for the new paths

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Issue #541 item 3 (owner-accepted 2026-10-13; scoping confirmed by the owner 2026-10-19 in the platform-planner-u24
terminal): add gitleaks (secrets) and Semgrep (static analysis) as a new workflow. It reports only at first, like Trivy
(ADR D3), costs $0 on GitHub runners, stays out of `test.yml` (testing's), and the workflow path is registered to
platform in the same PR (D8 staged registration, `docs/architecture/devops_plan_amendment_proposal.md`). It also closes
follow-up 2 of `docs/plans/agent_infrastructure/llm_security_mapping.md` ("run a secret scanner in CI on every PR").

**Gating decision (owner, 2026-10-19):** gitleaks runs on **every** PR and every push to `main`, because a secret can
land in any file (agent-working shards, handovers, docs). Semgrep is the path-gated part. A weekly scheduled run scans
the full history (gitleaks) and the whole tree (Semgrep).

## Scope
- `.github/workflows/security-scan.yml` (new):
  - triggers: `pull_request` (no `paths:` filter), `push` to `main`, `schedule` weekly, `workflow_dispatch`;
  - `permissions: contents: read` at the top; `security-events: write` only on the job that uploads SARIF, and the
    upload is guarded to same-repository PRs, push and schedule (a fork PR gets a read-only token; see
    `TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK`);
  - a concurrency group that cancels superseded PR runs only (the `iac.yml` pattern);
  - `runs-on: ubuntu-latest` (precheck decision; no pin);
  - **gitleaks job**: on PR and push, scans only the new commits (`--log-opts` over the PR base..head range or the
    push's before..after); on schedule and dispatch, the full history. Runs the pinned gitleaks release (binary with a
    verified SHA-256, or the image by digest) rather than `gitleaks/gitleaks-action`, so no licence key or token is
    involved. **`--redact` is mandatory**: logs, job summary and artifacts are public on this repository, so no
    finding may print the secret. `--exit-code 0` (report-only). Findings count + rule + file:line go to the job
    summary; the redacted JSON/SARIF report is uploaded as an artifact;
  - **Semgrep job**: runs when the PR changes code or config (`src/**`, `tools/**`, `frontend/**`, `docker/**`,
    `infra/**`, `.github/workflows/**`, `compose.yaml`, `*.py`), decided by a `git diff --name-only` step inside the
    job (no new marketplace action for path filtering); on push, schedule and dispatch it always runs. Semgrep CE
    pinned by version (pip with a hash, or the image by digest), registry rulesets only (security rulesets for
    Python, TypeScript, Dockerfile and GitHub Actions; exact list chosen in plan.md), no Semgrep login or app token,
    report-only (no `--error`). Findings summary in the job summary; SARIF uploaded to code scanning with its own
    `category: semgrep` (guarded as above) and as an artifact;
  - every `uses:` pinned by full commit SHA with a version comment, like `publish-images.yml` and `iac.yml`;
  - no `secrets.*` other than the default `GITHUB_TOKEN`.
- Any scanner config file the implementer needs (for example a gitleaks allowlist for known test fixtures) lives under
  `.github/` (not the repo root: `test_repo_root_allowlist`), and is registered to platform alongside the workflow.
- `registries/session_roles.yaml`: add `.github/workflows/security-scan.yml` (and any config path created above) to
  platform's `owns`; regenerate the session cards with `tools/sessions/generate_agents.py`;
  `python3 -m tools.sessions.route` returns platform for each new path.
- The PR body asks the owner to confirm the roles diff (D8), uses the D7 evidence labels ("written + validated" for
  local checks, "running on CI" for the PR's own run), and lists the first run's findings (redacted) as the baseline.
  Moving either scanner to blocking needs its own owner yes later (D3).

## Out of Scope
- Blocking on any finding (a later ticket, owner yes per D3).
- Any edit to `.github/workflows/test.yml` (testing's) or a new job there (CI-runtime epic).
- Project-specific Semgrep rules: per `docs/plans/codebase_health/python_code_craft_roadmap.md`, project rules are
  ast-grep (codebase domain); this lane uses registry security rulesets only.
- Fixing any finding the scanners report (findings are filed to the owning domain afterwards).
- Extending the local Bash secret-scan hook (llm_security_mapping follow-ups 3-4, agent-working's).
- Semgrep AppSec Platform / Pro rules, any paid service or app token.
- compose.yaml, docker/prometheus.yml, Grafana provisioning (ubuntu's step-2 files).

## Acceptance Criteria
- The PR's own CI runs `security-scan.yml`: the gitleaks job and the Semgrep job both run (the PR touches
  `.github/workflows/**`) and succeed while reporting; step conclusions read, not just the colour.
- A redaction check: the gitleaks report and job log contain no unredacted match (verified locally on a synthetic
  secret in a throwaway repo, never committed to this repository).
- The Semgrep path gate is shown both ways: the gate step's script, run locally against a docs-only file list and a
  code file list, skips with a "no code paths changed" summary line for the first and runs for the second.
- `grep -n "secrets\." .github/workflows/security-scan.yml` finds only `secrets.GITHUB_TOKEN`, or nothing.
- No `uses:` without a 40-char SHA; scanner versions pinned.
- `tests/static` passes; `tools/sessions/validate.py` reports 0 findings; the roles diff adds exactly the new paths.
- `.github/workflows/test.yml` is unchanged.

## Related Tickets
`TCK-20261014-IMAGE-SBOM-SCAN-SIGN` (Trivy report-only precedent), `TCK-20261018-IAC-WORKFLOW-AND-ROLES` (path-gated
workflow + D8 roles diff precedent), `TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK` (SARIF upload, fork guard),
`TCK-20261013-HARNESS-LLM-SECURITY-MAPPING` (follow-up 2), `TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24` (runner label).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D3, D7, D8), `docs/architecture/devops_plan_amendment_proposal.md`
(D8 supersession), `docs/plans/agent_infrastructure/llm_security_mapping.md`,
`docs/plans/codebase_health/python_code_craft_roadmap.md` (Semgrep CE vs ast-grep), GitHub issue #541 item 3.

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20261018-IAC-WORKFLOW-AND-ROLES/`,
`agent-working/stored_artifacts/TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK/`

## Related Code Areas
`.github/workflows/security-scan.yml` (new), `registries/session_roles.yaml`, generated session cards,
`.github/workflows/iac.yml` and `publish-images.yml` (patterns only, not edited), `tests/static/`

## Assumptions / Open Questions
- The repository is public and personal (`org=false`), so code scanning needs no licence; gitleaks is run as the
  binary/image anyway, so its action's org licence never applies.
- If a `tests/static` rule rejects the new workflow (for example an allowlist of workflow files or `uses:` strings),
  stop and report to platform-planner-u24: the fix may be in testing's or agent-working's files.
- If the first full-history gitleaks run finds a real live secret, stop and tell platform-planner-u24 and the user
  directly (rotation first); do not paste it anywhere.
- Dependabot's existing `github-actions` ecosystem picks up the new action pins; no `dependabot.yml` edit expected.

## Implementation Notes
Pins: gitleaks v8.30.1 (linux_x64 tarball, SHA-256 verified in the job), Semgrep CE 1.179.0 as the `semgrep/semgrep` image by digest
(`sha256:93963d92...e01b`); actions reuse the SHAs already in `iac.yml`. Semgrep rulesets: `p/python`, `p/typescript`, `p/dockerfile`,
`p/github-actions` (no login needed). gitleaks writes JSON (no SARIF upload: GitHub's own secret scanning owns that surface). A Semgrep SARIF
result carries no level, so the summary maps each result to its rule's default level (fixed after the first CI run showed zeros).
The workflow_dispatch/full-history baseline cannot run before merge (a dispatch needs the file on the default branch); the first weekly or manual run
after merge is the full-history baseline.

## Test Summary
validated (local): static shape (YAML, SHA pins, no `secrets.*`, no `--error`, `security-events` only on semgrep); redaction on a synthetic secret in a
throwaway repo (1 finding, 0 occurrences of the value in report or stdout); Semgrep gate both ways (docs-only: `run=false` + skip line; `src/a.py` and the
workflow file: `run=true`); `tests/static` 106 passed; session tests 776 passed; `tools.sessions.validate` 0 findings; route returns platform.
running on CI (PR #665, run 39226194890): gitleaks and semgrep jobs both success, every step success including SARIF upload. Baseline: gitleaks 0 findings
(PR commits); Semgrep 109 findings (23 error, 83 warning, 3 note by rule level), top rules github-actions-mutable-action-tag 64, run-shell-injection 11,
insecure-hash-algorithm-md5 9. Findings are to be filed to owning domains, not fixed here.

## Files Changed
.github/workflows/security-scan.yml (new); registries/session_roles.yaml; .claude/agents/session-platform-{planner,implementer}{,-u24}.md (regenerated);
docs/REGISTRY.yaml (regenerated).

## Completion Summary
Report-only gitleaks (every PR/push, redacted) and path-gated Semgrep CE workflow landed in PR #665 with the roles diff for owner confirmation.
Gap: the weekly/full-history baseline is unobserved until the first post-merge run. Semgrep baseline findings (mutable action tags, shell injection) need routing.

Pins: gitleaks 8.30.1 (`gitleaks_8.30.1_linux_x64.tar.gz`, SHA-256 `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`); Semgrep CE 1.179.0 image
`semgrep/semgrep@sha256:93963d9295a366f59e4850127b1550400ee7b388f04fe144e4a1f6325d96e01b`; `actions/checkout` `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1),
`actions/upload-artifact` `cf430e030ddbb5b0abf93d22962f4752f3646cd9` (v7.0.2), `github/codeql-action/upload-sarif` `24c54180a607b1449ed407dd24f251e4e9147c8d` (v4.38.3).
Redaction: with 8.30.1 the report has no key holding the raw line (Match and Secret are `REDACTED`); the public artifact is still jq-filtered to RuleID, File, StartLine, Commit, Fingerprint.
Capacity: each PR or push event now starts 1-2 more jobs (gitleaks always, Semgrep when the gate passes) against the 20-concurrent-job limit.
Gate status: the "Semgrep OSS" code-scanning check is not a required gate and can go red on a new error-level alert; it is advisory.
