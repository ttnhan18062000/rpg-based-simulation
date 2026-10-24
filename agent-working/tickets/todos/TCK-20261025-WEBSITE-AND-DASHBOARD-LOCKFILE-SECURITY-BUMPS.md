---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261025-WEBSITE-AND-DASHBOARD-LOCKFILE-SECURITY-BUMPS
phase: open
date: 2026-10-25
tags: [security, platform]
---

# TCK-20261025-WEBSITE-AND-DASHBOARD-LOCKFILE-SECURITY-BUMPS

## Title
Refresh website/ and dashboard-frontend/ npm lockfiles to clear their open Dependabot security alerts

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
This is the second half of the owner's 2026-10-24 Dependabot decision (#715 issuecomment-6385332339). The first half,
`uv.lock`, shipped in #736. Both lockfiles belong to lead-planner (`website/**` and `dashboard-frontend/**`). Open
alerts on main 3f4f3b84b, read 2026-10-25:

| lockfile | alerts | critical | notes |
|---|---|---|---|
| `website/package-lock.json` | 87 | 4 (proxy-addr, shell-quote, tinypool ×2) | Docusaurus docs site. Dependabot labels these "runtime", but the site is built to static files by `.github/workflows/deploy-docs.yml` (`npm ci` + `docusaurus build`), so they reach the build and dev server, not the browser. The largest groups are undici (21), fast-uri (8), js-yaml (7), brace-expansion (6) and joi (5). |
| `dashboard-frontend/package-lock.json` | 23 | 0 | All development-scope (vite, vitest, @vitest/mocker, undici, postcss, browserslist, source-map-js, baseline-browser-mapping). |

`frontend/package-lock.json` (rpg) is out of scope; it was relayed to rpg on PR #565.

## Scope
- In each of `website/` and `dashboard-frontend/`, run `npm audit fix` (no `--force`), then `npm audit` to list what
  remains. For an alert the plain fix can't reach (a transitive pin), use an `overrides` entry in that `package.json`
  pinned to the first patched version. Only for the alerted package, and with lead-planner review of the exact diff.
- No major-version bump of a direct dependency (Docusaurus, React, Vite, Vitest) unless an alert can't be cleared
  otherwise. In that case, stop and send lead-planner the before/after first.
- Verify:
  - `website`: `npm ci && npm run build` succeeds.
  - `dashboard-frontend`: `npm ci && npm run build && npm test` succeeds.
  - Run them one at a time in a lead-granted slot, under `systemd-run` MemoryMax.
- After merge, confirm on GitHub that the alerts for both lockfiles close, or list each one left with its reason.

## Out of Scope
- `frontend/package-lock.json` (rpg) and `requirements-knowledge.txt` (agent-working).
- Any change to site content, dashboard code or the deploy workflow.
- Packages without an open alert. Don't run a blanket `npm update`.

## Acceptance Criteria
- [ ] Both lockfiles are regenerated. `git diff` touches only the two `package-lock.json` files, plus `package.json`
      only for reviewed `overrides`.
- [ ] `website` builds. `dashboard-frontend` builds, and its tests pass.
- [ ] `npm audit` output before and after, per lockfile, is in the ticket. Every critical and high alert is cleared, or
      listed with the reason it can't be.
- [ ] After merge, the open Dependabot alerts for both lockfiles are 0, or every one left is listed with its reason.

## Related Tickets
- `TCK-20261024-UV-LOCK-SECURITY-BUMPS` (#736): the uv.lock half.

## Related Docs
- `.github/workflows/deploy-docs.yml` (website build).

## Related Stored Artifacts
- None.

## Related Code Areas
- `website/package.json`, `website/package-lock.json`, `dashboard-frontend/package.json`,
  `dashboard-frontend/package-lock.json` (lead-planner's files).

## Assumptions / Open Questions
- Alert counts are GitHub's as of 2026-10-25. Re-read them when starting.
- `npm` is available on this host (the dashboard has a `node_modules/`). Check `node --version` against the CI
  workflow's pin before regenerating, so the lockfile format matches.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
