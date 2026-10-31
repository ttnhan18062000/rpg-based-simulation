---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [ai, governance, delivery]
---

# Ruleset export and login-assumption inventory

Result record for `TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY` (plan section 54, items 3-4). Everything here was read with GET calls only. No tool, setting, credential or ruleset was changed.

## 1. Ruleset export (the rollback point)

- File: `ruleset_14220945_export.jsonl` (one JSON line, keys sorted). Read on 2026-10-31 against `origin/main` `6fdfdf5556548105e28ab370832f36bc96241561`.
- The repository has exactly one ruleset: `protect_branches`, id 14220945, target `branch`, enforcement `active`.
- Content: it applies to `~DEFAULT_BRANCH` with no exclusions; rules `deletion`, `non_fast_forward`, `update` and `required_status_checks` (strict off; contexts `Code health` and `Type check`); one bypass actor, role id 5 (the repository Admin role), mode `always`.
- **Removed field:** `current_user_can_bypass`. It describes the caller, not the ruleset, so it would show a false change whenever the reader's role differs. A later comparison against a fresh read ignores that one field and nothing else.
- **How the export was read:** with an admin-level login. A lower-role read may not return `bypass_actors`; whether it does is **unverified** (not traced to GitHub's documentation, not tried). A compare run under a machine user could therefore show a difference that is not a ruleset change. Compare under the same role, or treat a missing `bypass_actors` as "not returned", not "removed".
- No ruleset covers tags. Tags are unprotected until `TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION`.

Comparison recipe: `gh api repos/{owner}/{repo}/rulesets/14220945`, drop `current_user_can_bypass`, sort keys, compare to the export.

## 2. Repository-level Actions secrets

`GET .../actions/secrets` returned `total_count` 0: **none**. (Nothing further is recorded here.)

## 3. Tools that assume the owner login or an admin-only endpoint

Method: read each caller's code for the `gh` verbs and API paths it uses. "Under a write-role machine user" is a prediction from those paths, **unverified** unless a row says otherwise: no tool was run under another identity.

| Tool | What it calls | Admin or owner-only? | Behaviour under a write-role machine user |
|---|---|---|---|
| `tools/delivery/pr_render.py` | `gh pr view` (for `--check`); the rest is local `git` | No | Read of a public repo's PR: expected to work. Unverified. |
| `tools/delivery/pr_status.py` | `gh pr view`, `gh pr checks`, `GET repos/{owner}/{repo}/actions/runs`, `.../actions/runs/{id}/jobs`, `.../actions/jobs/{id}`, `.../check-runs/{id}/annotations` | No admin endpoint; reads Actions and checks | Expected to work if the credential carries read access to Actions and checks; a credential without it would make the verdict `UNKNOWN`, which the tool already treats as not green. Unverified. |
| `tools/delivery/delivery_cost_measurement.py` (`--rework`) | `GET .../actions/runs`, `.../pulls` (paged) | No | Expected to work (read). Unverified. |
| `tools/agent-monitoring/batch_latency.py` | `gh pr view --json commits,mergedAt,statusCheckRollup` | No | Expected to work (read). Unverified. |
| `tools/sessions/prune_branches.py`, `status.py`, `launch.py` | `gh pr list` / `gh pr view` | No | Expected to work (read). Unverified. |
| `tools/sessions/session_start_hook.py` | `gh issue list --label for:<role>`; fails open when `gh` is missing, unauthenticated, offline or slow | No | Reads issues; fails open, so a failure shows as no messages, not an error. |
| `tools/test_architecture/slow_regression_gate.py`, `slow_regression_watchdog.py` | `gh run list`, `gh run view`, `gh workflow run slow-regression.yml` | `workflow run` is a write on Actions | The watchdog dispatches a run: needs write access to Actions. Runs in CI with the workflow's own token (`actions: write`), not a person's login. Unverified for a person-held machine user. |
| `tools/test_architecture/slow_regression_report.py` | Issue and comment reads and writes through `gh`; filters comments by a fixed bot login | Writes issues | Runs in CI with the workflow token. Its comparison against a fixed bot login assumes the author identity of its own comments; a machine user posting by hand would not match. |
| `.github/workflows/slow-regression-watchdog.yml` | `gh api .../commits/main`, `gh workflow run` with `${{ github.token }}` | No person's login | Independent of any person's credential. |
| `.github/workflows/deploy-docs.yml` | Comment only (Pages not enabled) | No | Not applicable. |
| GitHub MCP server (`.mcp.json`, `github`) | Runs a container that takes its credential from an environment file the launcher supplies | Scope set by whichever credential the file holds | Behaviour is the credential's scope. Contents were not read. It failed to connect in this session; cause not investigated. |
| `gh pr create`, `gh pr merge` (agents' own commands) | Not tool code; the permission rules allow `gh pr create`, ask on `gh pr merge` | Merge needs the Admin role today (ruleset bypass) | A write-role user could open a PR; merging under the same ruleset is the owner's call. Unverified. |

Not found in tool code: any use of the ruleset endpoints, the repository's collaborators endpoint, or any admin-only path. Nothing here reads the ruleset except this record.

## 4. Left out on purpose

Host credential stores and E6a step 3 (owner-only reports), and anything about credentials' values, scopes or locations.

## 5. Result against the acceptance criteria

1. The export parses (JSON, 13 keys) and can be compared with a fresh read, ignoring only `current_user_can_bypass`.
2. Every row in section 3 has a stated behaviour, each marked as unverified where it was not run.
3. No credential value, store location or host detail appears here.
