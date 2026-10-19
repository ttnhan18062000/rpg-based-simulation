---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW
phase: open
date: 2026-10-19
tags: [platform, delivery, security]
---

# TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW

## Title
CI: .github/workflows/security-scan.yml — gitleaks (secrets) on every PR and Semgrep (static) path-gated, both report-only, plus the roles diff for the new paths

## Status
OPEN

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
(filled by the implementer)

## Test Summary
(filled by the implementer)

## Files Changed
(filled by the implementer)

## Completion Summary
(filled by the implementer)
