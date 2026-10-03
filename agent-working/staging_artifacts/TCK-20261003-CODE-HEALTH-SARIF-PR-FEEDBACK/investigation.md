---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
artifact_type: investigation
tags: [delivery, security]
---

# Investigation — TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK

Context scan: `search_docs` (no relevant hit; the security-reviewer agent doc only) and `graphify query` (no nodes) first; the facts below are from the follow-up reads and runs.

## Repository and token facts
- The repository is **public** (`gh repo view`), so code scanning needs no licence. `code-scanning/default-setup` is `not-configured` and there is no analysis yet (HTTP 404 "no analysis found"); uploading third-party SARIF does not need default setup. Whether the upload is accepted is only proven by the first PR run (risk below).
- Default workflow token permission is `read` (`actions/permissions/workflow`), and `test.yml` has no `permissions:` block. A job that uploads needs `security-events: write` (and `contents: read`) set at job level only; nothing else changes.
- A `pull_request` run from a **fork** gets a read-only token, so an upload would fail with "Resource not accessible by integration"; the upload must be guarded to same-repository PRs.

## What the tools emit (ruff 0.16.10, complexipy 8.0.1)
- `ruff check <files> --output-format sarif`: SARIF 2.1.0, one run, `results[].ruleId` is the rule **name** (`blind-except`), not the code (`BLE001`) that registry rows use; `locations[].physicalLocation.artifactLocation.uri` is an absolute `file:///...` path (code scanning needs repository-relative). `ruff rule --all --output-format json` lists 971 rules with `name` and `code`, which gives the name -> code map offline.
- `complexipy <files> -q --output-format sarif --output F`: SARIF 2.1.0, `ruleId` `CC001`, uri already relative (`uriBaseId %SRCROOT%`), `logicalLocations[].name` is `Class::method` (registry symbol is `Class.method`), complexity only in the message text ("has a cognitive complexity of 20, which exceeds the maximum allowed complexity of 15."), only functions over the limit are reported.
- Registry keys (the ratchet's): ruff `(file, None, "ruff", <code>)` with value = count of that rule in the file; complexipy `(file, "Class.method", "complexipy", "cognitive-complexity")` with value = complexity.

## Design consequences
- SARIF results carry no baseline identity, so the filter works per ratchet unit: a ruff `(file, code)` group is dropped when its count is at or below its row's ceiling, and kept whole when it is over the ceiling or has no row (the SARIF cannot say which finding is the new one; GitHub shows PR-diff alerts inline and the rest in the code-scanning tab). A complexipy result is dropped when its complexity is at or below its row's ceiling.
- Counts need the whole file, which ruff gives (it checks whole files); only changed `src/**/*.py` files are scanned, as the registry covers `src/` only.
- Limits: code scanning accepts up to 5,000 results per run and 10 MB; the filter caps and reports truncation.
- Pinning: `github/codeql-action/upload-sarif` latest is v4.38.2 (commit 2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2, resolved with the commits API). Pin by full commit SHA with the version in a comment (stronger than a tag for a write-scoped action).
- Existing pins to update: `tests/static/test_ci_step_summary_reporting.py` `_PRE_EXISTING_USES` (exact allowlist of `uses:` strings); `tests/static/test_ci_uv_install.py` (one locked `uv sync` per Python job; `_LINT_JOBS`).
- Open measurement: wall time of ruff and complexipy SARIF on a typical changed-file set (expected seconds).
