---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW
artifact_type: plan
tags: [platform, delivery, security]
---

# Plan: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW

## Steps
1. **Pick pins.** gitleaks: latest stable release at least two weeks old; record version + SHA-256 of the
   linux_x64 tarball (or the `ghcr.io/gitleaks/gitleaks` image digest). Semgrep CE: latest stable at least two weeks
   old; pip install with `--require-hashes` from a small pinned requirements block, or the `semgrep/semgrep` image by
   digest. `actions/checkout`, `actions/upload-artifact`, `github/codeql-action/upload-sarif`: reuse the SHAs already
   pinned in `publish-images.yml`/`iac.yml`/`test.yml`; do not introduce a second pin of the same action.
2. **Write `.github/workflows/security-scan.yml`** on the `iac.yml` shape:
   - header comment: purpose, ticket id, ADR D3 (report-only), owner gating decision 2026-10-19;
   - `on`: `pull_request`, `push: branches: [main]`, `schedule` (one weekly cron, off-peak), `workflow_dispatch`;
   - `permissions: contents: read`; concurrency `security-scan-${{ github.ref }}`, cancel only for `pull_request`;
   - job `gitleaks`: checkout with `fetch-depth: 0`; compute the range (PR: `base.sha..head.sha`; push:
     `before..after`, falling back to full history when `before` is all zeros; schedule/dispatch: full history);
     run `gitleaks git --redact --exit-code 0 --report-format sarif|json --report-path ...` with `--log-opts` for the
     range; summary step prints count, rule id, file:line (never the match); upload the report as an artifact.
     No SARIF upload for gitleaks (secret alerts belong to GitHub's own secret scanning, and a redacted finding in the
     Security tab adds nothing the summary lacks);
   - job `semgrep`: checkout; a gate step that computes changed files (PR: `git diff --name-only base...head`) and sets
     `run=true|false` against the code-path list in the ticket; push/schedule/dispatch always `run=true`. When false,
     write "Semgrep skipped: no code paths changed" to the summary and stop (no SARIF upload). When true:
     `semgrep scan --config <rulesets> --sarif --output semgrep.sarif --metrics=off` (no `--error`), summary step
     (count by severity + top rules), upload the artifact, then `upload-sarif` with `category: semgrep` under
     `security-events: write` (job-level), guarded by
     `github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository`.
   - Ruleset starting point: `p/python`, `p/typescript`, `p/dockerfile`, `p/github-actions`, `p/secrets` off (gitleaks
     covers it). Adjust only if a ruleset needs login; record the final list in Implementation Notes.
3. **Roles diff**: add `.github/workflows/security-scan.yml` (and any `.github/` config file created) to platform's
   `owns` in `registries/session_roles.yaml`; run `python3 tools/sessions/generate_agents.py`; commit the regenerated
   cards.
4. **Validate locally** (test_plan.md), then open the PR from the implementer's own `-u24` branch.
5. **PR**: body asks the owner to confirm the roles diff, lists the first run's redacted findings per scanner as the
   baseline, uses D7 labels; read the run's step conclusions before claiming "running on CI".
6. **Close** per CLAUDE.md "After Work" (hand-orchestrated closure tool, done_checker_static, mechanism-registry
   advisory).

## Scope guards
- Never edit `test.yml`. Never add `--error` or a non-zero exit to either scanner.
- Never print an unredacted match anywhere (log, summary, PR body, ticket). If a live secret appears, stop and tell
  platform-planner-u24 and the user.
- No repo-root files. No new marketplace action beyond what is listed in step 1.

## Acceptance-criteria map
| AC | Step |
|---|---|
| PR CI runs both jobs, steps succeed | 2, 5 |
| Redaction check | 2, test_plan T2 |
| Semgrep gate both ways | 2, test_plan T3 |
| No `secrets.*` beyond GITHUB_TOKEN | 2, test_plan T1 |
| SHA pins / version pins | 1, test_plan T1 |
| tests/static + validate.py + exact roles diff | 3, test_plan T4 |
| test.yml unchanged | guard, test_plan T4 |
