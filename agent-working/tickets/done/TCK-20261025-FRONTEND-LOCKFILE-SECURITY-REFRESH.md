---
status: historical
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH
phase: done
date: 2026-10-25
tags: [security]
---

# TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH

## Title
Refresh frontend/package-lock.json inside the current major versions to clear its open Dependabot security alerts

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Owner direction 2026-10-25, Lane U1 (#715 issuecomment-6393397119, confirmed in rpg-planner-ubuntu's terminal; the
relay came from lead-planner and the finding is on PR #565 issuecomment-6385352678). `frontend/package-lock.json` has
56 open Dependabot alerts on main bd296f58a, all development-scope:

- 1 critical: vitest, fixed in 4.1.0.
- 21 high: vite (fixed in 7.3.7), rollup (4.59.0), postcss (8.5.18), undici (7.30.1), js-yaml (4.3.2), minimatch
  (3.1.3 and 9.0.7), brace-expansion (1.1.16 and 2.1.2), browserslist (4.28.7), flatted (3.4.2), nanoid (3.3.12) and
  source-map-js (1.2.2).
- The rest are medium and low, among them @vitest/mocker 4.1.12, vitest 4.1.11, @babel/core, esbuild, picomatch,
  @humanfs/node and baseline-browser-mapping.

Every fix is inside the current major of the direct dependency (vite 7, vitest 4), so this ticket needs no major move.
The major moves are in `TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES`.

The owner chose one superseding PR. This ticket supersedes dependabot PR #565 (the npm-minor-patch group,
19 updates).

## Scope
- In `frontend/`, under Node 24 (`/data/vboxuser/node24/bin` on PATH, for the npm commands only), run `npm audit fix`
  without `--force`. Then run `npm audit` to list what is left.
- Bump the direct devDependencies with alerts (`vite`, `vitest`) to their patched in-major versions in `package.json`.
  For a transitive alert the plain fix can't reach, add a nested `overrides` entry pinned to the first patched
  version, for the alerted package only. Send rpg-planner-ubuntu the exact `package.json` diff before committing it.
- Take #565's in-range updates only where they are needed to clear an alert. Don't run a blanket `npm update`.
- Verify, in a heavy-run slot from lead-planner, under `systemd-run --user --scope -p MemoryMax=3G`, with any temp
  directory on /data outside the repo: `npm ci && npx vitest run && npm run build` (this is what CI's `frontend` job
  runs; `frontend/package.json` has no `test` script, so `npm test` fails). Also run `npm run lint` and report
  whether the result is the same as before the change.

## Out of Scope
- Major-version moves of any direct dependency: vite 8, vitest 5, @vitejs/plugin-react 6, eslint 10 and lucide-react 1
  are all in `TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES`.
- Any change to `frontend/src/**`, test code, configs or CI workflows.
- The `website/`, `dashboard-frontend/` and `uv.lock` lockfiles (lead-planner's; #738).

## Acceptance Criteria
- [x] `git diff` touches only `frontend/package-lock.json`, plus `frontend/package.json` for the in-major version
      bumps and any `overrides` rpg-planner-ubuntu reviewed.
- [x] `npm ci`, `npx vitest run` and `npm run build` pass under Node 24. `npm run lint` is the same as before or
      better.
- [x] `npm audit` output before and after is summarized in this ticket. Every critical and high alert is cleared, or
      listed with the reason it can't be.
- [ ] Dependabot PR #565 is closed with a comment pointing to the superseding PR. The owner or rpg-planner-ubuntu
      closes it once the PR exists.
- [ ] After merge, the open Dependabot alerts on `frontend/package-lock.json` are 0, or each one left is listed with
      its reason.

## Related Tickets
- `TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES`: the major moves. A follow-up PR after this one merges (owner, #715 issuecomment-6393490542).
- `TCK-20261025-WEBSITE-AND-DASHBOARD-LOCKFILE-SECURITY-BUMPS` (#738): the same shape for website/ and
  dashboard-frontend/.
- `TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP`: CI's `frontend` job (`npm ci`, `npx vitest run`, `npm run build`).

## Related Docs
- `.github/workflows/test.yml` (`frontend` job, Node 24).
- `.github/dependabot.yml` (the `/frontend` npm entry, grouped into npm-major and npm-minor-patch).

## Related Stored Artifacts
- None.

## Related Code Areas
- `frontend/package.json`, `frontend/package-lock.json`.

## Assumptions / Open Questions
- These alert counts are GitHub's, read on 2026-10-25. Re-read them when you start:
  `gh api 'repos/{owner}/{repo}/dependabot/alerts?state=open&per_page=100' --paginate`, filtered on
  `manifest_path` starting with `frontend/`.
- npm audit counts every vulnerable path, and Dependabot counts one alert per package and advisory pair, so the two
  numbers won't match (seen on #738).
- `docker/frontend.Dockerfile` builds on node:24.21.0, so a lockfile written by npm 11 under Node 24 suits both CI and
  the image.
- The host's disk had about 9 GB free. Delete `frontend/node_modules/` once the PR merges.

## Implementation Notes
- Branch `frontend-lockfile-security-refresh` from ca7dadb75 (`frontend-dependency-security` is checked out in the planner worktree).
- `npm audit fix` (no --force) under Node 24.22.1 / npm 11.19.1 cleared every alert; no `overrides` needed.
- `package.json`: vite `^7.2.4` -> `^7.3.7`, vitest `^4.0.18` -> `^4.1.12` (floors raised so the manifest cannot resolve a vulnerable version). Lockfile regenerated with `npm install --package-lock-only`.
- Resolved: vite 7.3.7, vitest 4.1.12, rollup 4.65.0, postcss 8.5.31, undici 7.30.1, js-yaml 4.3.2, esbuild 0.28.2 (inside vite's `^0.27 || ^0.28`).
- Dependabot open alerts on `frontend/` read 55 on 2026-10-25 (ticket text said 56).

## Test Summary
- `npm audit` before: 20 vulnerabilities (1 critical, 13 high, 4 moderate, 2 low). After: 0.
- Before (unchanged main): vitest 31 files / 369 tests pass; build OK; lint exit 1, 21 problems (18 errors, 3 warnings).
- After: `npm ci` OK; vitest 31 files / 369 tests pass; build OK; lint exit 1, identical output (21 problems).

## Files Changed
- frontend/package.json, frontend/package-lock.json

## Completion Summary
Frontend lockfile refreshed in-major: `npm audit` 20 vulnerabilities -> 0, vite ^7.3.7 / vitest ^4.1.12 floors, vitest/build pass, lint unchanged from baseline (21 problems). Closing #565 and verifying the post-merge alert count remain with the owner/planner after merge.
