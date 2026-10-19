---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW
artifact_type: test_plan
tags: [platform, delivery, security]
---

# Test plan: TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW

Evidence labels (ADR D7): T1-T4 are "validated (local)"; T5 is "running on CI".

- **T1 — static shape.** YAML parses; `grep -n "secrets\." .github/workflows/security-scan.yml` shows nothing but
  `GITHUB_TOKEN`; every `uses:` line has a 40-hex SHA and a version comment; no `--error` and every scanner call has
  exit code 0; top-level `permissions` is `contents: read`; `security-events: write` appears only on the semgrep job.
  `actionlint` on the file if available locally (report its output either way).
- **T2 — redaction.** In a throwaway repo under the scratchpad (never in this repository), commit a synthetic
  secret-shaped string, run the pinned gitleaks with the workflow's exact flags, and check the report and stdout
  contain no part of the string. Record the command and result, not the string.
- **T3 — Semgrep path gate.** Run the gate step's script locally with a docs-only file list
  (`docs/x.md`, `agent-working/tickets/y.md`) → `run=false` and the skip line; with a code list (`src/a.py`) →
  `run=true`; with `.github/workflows/security-scan.yml` → `run=true`.
- **T4 — repo checks.** `pytest tests/static -q`; `python3 tools/sessions/validate.py` (0 findings);
  `python3 -m tools.sessions.route .github/workflows/security-scan.yml` → platform; the session-card/registry tests
  (`pytest tests/tools/test_session_cards.py tests/tools/test_session_u24_twins.py -q` and any `test_session_roles*`);
  `git diff origin/main -- .github/workflows/test.yml` is empty; the roles diff adds exactly the new paths.
- **T5 — PR CI.** On the PR's own run: gitleaks job and semgrep job both run (the PR touches `.github/workflows/**`),
  each step's conclusion read via `gh run view --json jobs`; artifacts downloaded and their finding counts quoted in
  the PR body as the baseline (redacted); the SARIF upload step succeeded (same-repo PR).
