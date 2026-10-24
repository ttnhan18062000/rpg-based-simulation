---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261024-UV-LOCK-SECURITY-BUMPS
phase: open
date: 2026-10-24
tags: [security, platform]
---

# TCK-20261024-UV-LOCK-SECURITY-BUMPS

## Title
Bump the Python packages in uv.lock that have open Dependabot security alerts to their first patched versions

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
GitHub Dependabot reports 27 open alerts on `uv.lock`: 2 critical, 11 high, 12 medium and 2 low, read on main
42c2e2b4e on 2026-10-24. Every one except GHSA-gvp8-978c-rx2q (PyJWT, no patched version listed, but its range
`>= 2.11.0, <= 2.13.0` is left behind by the bump) has a first patched version. Owner decision 2026-10-24
("go with your recommendation"), logged on #715 (issuecomment-6385332339): lead-planner files this ticket, and
codebase-implementer implements it after M7 batch 1 merges. `uv.lock` and `pyproject.toml` are lead-planner's files.
lead-planner reviews the diff.

Locked version → minimum target, with what pulls the package in (from `uv.lock`):

| package | locked | target (≥) | alerts | pulled in by | ships in the backend image? |
|---|---|---|---|---|---|
| urllib3 | 2.6.3 | 2.8.0 | 4 high, 1 medium | `requests` (runtime dep) | **yes** |
| certifi | 2026.2.25 | 2026.10.19 | 1 critical | `requests`, `httpx`, `httpcore`, `geventhttpclient` | **yes** |
| idna | 3.11 | 3.15 | 1 medium | `requests`, `httpx`, `anyio` | **yes** |
| pyjwt | 2.13.0 | 2.15.0 | 1 critical, 6 high, 8 medium | `mcp` (`search-mcp` extra, `dev` group) | no |
| cryptography | 49.0.0 | 50.0.0 | 1 high | `pyjwt[crypto]` | no |
| mcp | 1.28.1 | 1.30.0 | 1 medium | `search-mcp` extra, `dev` group | no |
| pygments | 2.19.2 | 2.20.0 | 1 low | `pytest`, `rich`, `textual` | no |
| setuptools | 81.0.0 | 83.0.0 | 1 medium | `torch` | no |
| torch | 2.12.1 | 2.13.0 | 1 low | `sentence-transformers` (`knowledge` extra) | no |

The backend image runs `uv sync --locked --no-default-groups` (`docker/backend.Dockerfile:25,31`), so only urllib3,
certifi and idna reach it. CI installs the dev group (`.github/workflows/test.yml`), so all nine reach CI.

## Scope
- `uv lock --upgrade-package <name>` for each of the nine packages, to at least the target above. Prefer the
  smallest upgrade that clears the alert. Don't run a blanket `uv lock --upgrade`.
- Raise a lower bound in `pyproject.toml` only where a direct dependency's floor would still allow a vulnerable
  version, and only for these packages. Send the exact before/after to lead-planner first.
- Re-run the checks a dependency bump can break: `uv sync --locked`, the scoped not-slow unit/integration
  suites, `tests/api`, the search-server tests (mcp, pyjwt), mypy and code health (0 new). Run them one at a
  time under `systemd-run` MemoryMax, in a lead-granted slot.
- After the PR merges, confirm on GitHub that the 27 uv.lock alerts close, or list any that stay open and why.

## Out of Scope
- `website/package-lock.json` and `dashboard-frontend/package-lock.json`: a second ticket, after this one.
- `frontend/package-lock.json` (rpg) and `requirements-knowledge.txt` (agent-working): relayed to their owners as
  findings.
- Any package without an open alert, and any major-version move not needed to clear an alert.
- Changing how torch is sourced. `pyproject.toml:34-38` keeps uv.lock on the PyPI torch build. If torch 2.13.0
  can't be locked without touching that, leave torch and setuptools at their current versions, record why in this
  ticket, and close the rest.

## Acceptance Criteria
- [ ] `uv.lock` has urllib3 ≥ 2.8.0, certifi ≥ 2026.10.19, idna ≥ 3.15, pyjwt ≥ 2.15.0, cryptography ≥ 50.0.0,
      mcp ≥ 1.30.0, pygments ≥ 2.20.0, and setuptools ≥ 83.0.0 / torch ≥ 2.13.0 (or the recorded torch exception).
- [ ] `git diff uv.lock` touches only these packages plus the dependencies they themselves require. Each other
      package that moves is named in the PR with its reason.
- [ ] `uv sync --locked` succeeds. The scoped suites pass, mypy shows 0 new, and code health shows 0 new / 0 worse.
- [ ] The backend image still builds (`docker build -f docker/backend.Dockerfile .`), if a slot allows. Otherwise
      the PR says it was not run, and CI's image job speaks for it.
- [ ] After merge, the open uv.lock Dependabot alerts are 0, or every one left is listed with its reason.

## Related Tickets
- M7 batch 1 (`TCK-20261024-API-SERVER-*`): this ticket is dispatched after it merges.

## Related Docs
- `pyproject.toml` comments at lines 34-38 (torch source and the knowledge stack).
- `docs/guides/delivery_process.md` (PR lifecycle).

## Related Stored Artifacts
- None.

## Related Code Areas
- `uv.lock`, `pyproject.toml` (lead-planner's files), `docker/backend.Dockerfile` (read only).

## Assumptions / Open Questions
- The alert list is GitHub's as of 2026-10-24. New alerts may appear before implementation. Re-read
  `gh api repos/{owner}/{repo}/dependabot/alerts?state=open` and the uv.lock rows when starting.
- PyJWT 2.15.0 must exist on PyPI. If the newest available is 2.14.x, take it and list GHSA-42vr-xj54-vc7v and
  GHSA-x33g-cr3x-6449 (fixed in 2.15.0) as remaining.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
