---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW
artifact_type: investigation
tags: [platform, delivery, security]
---

# Investigation: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW

Context scan (platform-planner-u24, 2026-10-19): `search_docs` ("gitleaks Semgrep secret scanning SAST workflow
report-only") and `graphify query` (no relevant nodes) first; the facts below are from the follow-up reads.

## What exists
- No scanner in CI: `.github/` has no gitleaks, semgrep or `.gitleaks.toml` file
  (`docs/plans/agent_infrastructure/llm_security_mapping.md` LLM02/LLM03 rows; confirmed with `ls`). Follow-up 2 there
  asks for a secret scanner on every PR, platform domain.
- The only secret scan is the advisory Bash PreToolUse hook (`tools/write_path_guard.py::scan_for_secrets`), Bash
  commands only.
- Workflows today: `deploy-docs.yml`, `iac.yml`, `pr-body-lint.yml`, `publish-images.yml`, `rpg-gate-report.yml`,
  `slow-regression*.yml`, `test.yml`. Platform owns `publish-images.yml`, `deploy-docs.yml`, `iac.yml`.
- Report-only precedent: Trivy in `publish-images.yml` (exit-code 0, summary step, ADR D3) and `trivy config` in
  `iac.yml`. `iac.yml` is the shape to copy: header comment naming the ticket and ADR, top-level
  `permissions: contents: read`, concurrency group cancelling PR runs only, pinned tool versions in `env`, SHA-pinned
  actions.
- SARIF precedent: `test.yml`'s `code-health-sarif` job (`TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK`): job-level
  `security-events: write`; fork PRs get a read-only token so upload is guarded to same-repo PRs; an empty SARIF
  upload clears the PR's earlier alerts, so do not upload an empty one for a skipped scan. `github/codeql-action/upload-sarif`
  pin there (reuse it).
- Repository: `ttnhan18062000/...`, PUBLIC, personal (not an org). Code scanning is free. gitleaks-action needs a
  licence only for org repos, but the ticket runs the gitleaks binary/image anyway.
- Logs and artifacts of a public repo's Actions runs are readable by anyone: gitleaks must run with `--redact`.
- Semgrep CE vs ast-grep: `docs/plans/codebase_health/python_code_craft_roadmap.md` picked ast-grep for
  project-specific rules (codebase domain) with Semgrep CE as the alternative. This ticket uses Semgrep only for
  registry security rulesets, so the two do not overlap. codebase-planner gets an fyi.
- `tests/static/test_ci_step_summary_reporting.py` is scoped to `test.yml`'s fast-lane jobs (its banned-action check
  names `test.yml`); confirm no other `tests/static` file globs all workflows before the PR.
- `test_repo_root_allowlist` (`docs/guidelines/repo_tooling_layout.md`): a new root entry (for example `.gitleaks.toml`)
  fails it, as `infra` did in the iac PR. Keep config under `.github/`.
- `tools/sessions/validate.py` requires every owned glob to match an existing file, so the roles diff goes in the same
  PR that creates the workflow (D8 staged registration).
- Dependabot already has a `github-actions` ecosystem in `.github/dependabot.yml`, so new action pins are covered.
- CI-runtime epic (testing's): no job is added to `test.yml`; a separate workflow running in parallel is fine
  (lead-planner-u24, 2026-10-19).

## Owner decisions
- 2026-10-13: #541 item 3 accepted (new path-gated, report-only workflow; not in test.yml; register path in same PR).
- 2026-10-19: scoping confirmed; gitleaks on every PR (not path-gated), Semgrep path-gated, weekly full run.
