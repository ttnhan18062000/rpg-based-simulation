---
status: historical
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES
phase: done
date: 2026-10-25
tags: [security]
---

# TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES

## Title
Decide each open frontend major-version Dependabot PR (#567, #568, #569, #570) one at a time, landing the ones that pass build, tests and lint

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner direction 2026-10-25, Lane U1 (#715 issuecomment-6393397119). The owner wants major moves reviewed one by one,
the majors shipping in their own PR after the refresh PR #739 merged (#715 issuecomment-6393490542), with each dependabot PR closed and a reason given. Four major-version dependabot PRs are open
on `frontend/`:

| PR | move | scope | what the 2026-10-25 check found |
|---|---|---|---|
| #570 | lucide-react 0.563 → 1.55 | **runtime** (ships in the bundle) | Peers on React 16-19 are fine. 12 files under `frontend/src` import 32 icons, among them `Home` and `BarChart3`, which are older alias names. 1.0 may have dropped aliases, and `tsc -b` in `npm run build` catches a missing export. |
| #569 | eslint 9.39 → 10.12 | dev | `frontend/eslint.config.js` is already a flat config. typescript-eslint and eslint-plugin-react-hooks latest accept eslint 10. Check `eslint-plugin-react-refresh` and `@eslint/js`. |
| #568 | vitest 4.0 → 5.0.3 | dev | Peers accept vite 7. It needs Node ^22.12 or 24 (CI and the image are on 24). Not needed for security: the critical alert is fixed in 4.1.0, which the refresh ticket handles. |
| #567 | @vitejs/plugin-react 5.1 → 6.1.2 | dev | **Needs vite ^8.0.0**, so it brings a vite 7 → 8 major (Rolldown) that no dependabot PR proposes. |

## Scope
`TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH` shipped in #739 (main 5fe577688); work on a new branch from origin/main. Take the moves one at a time,
in this order: lucide-react, eslint, vitest, then plugin-react with vite 8. For each:

1. Apply the move alone: the version in `package.json`, `npm install` under Node 24, plus any peer bump it strictly
   needs.
2. Run `npx vitest run`, `npm run build` and `npm run lint`, in a heavy-run slot from lead-planner, under
   `systemd-run --user --scope -p MemoryMax=3G`.
3. Report to rpg-planner-ubuntu: the diff, what passed or failed, and any source or config change the move would
   need. **Change no `frontend/src/**` code or config file until rpg-planner-ubuntu answers.** A rename such as a
   lucide alias is a code change and needs the same answer first.
4. On rpg-planner-ubuntu's go, commit the move as its own commit. On a no-go, revert it and record the reason here.
   That reason becomes the closing comment on the dependabot PR.

The default for #567 (plugin-react 6 plus vite 8): try it and report. If it needs more than version bumps (a config
rewrite, or a failing build or test), park it with a reason. Don't push it through.

## Out of Scope
- The in-major security refresh (`TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH`).
- Any frontend feature, refactor or behaviour change beyond what a go'd move strictly needs.
- Bumping other majors that no open dependabot PR proposes, except a peer bump a move strictly needs (such as vite 8
  for #567).

## Acceptance Criteria
- [x] Each of #567, #568, #569 and #570 has a recorded decision in this ticket: landed (with its commit), or parked
      (with its reason).
- [x] Each landed move is its own commit, and after it `npx vitest run`, `npm run build` and `npm run lint` pass
      under Node 24, with lint no worse than before.
- [x] No `frontend/src/**` or config change lands without rpg-planner-ubuntu's go for that move.
- [ ] After this ticket's PR merges, each dependabot PR is closed with a comment that gives its decision and points
      to the PR. For a parked move, the comment says what would unblock it.
- [x] No new Dependabot alert opens on `frontend/package-lock.json` because of a landed move.

## Related Tickets
- `TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH`: shipped in #739 (main 5fe577688).
- `TCK-20261025-WEBSITE-AND-DASHBOARD-LOCKFILE-SECURITY-BUMPS` (#738): the shape this follows (majors reviewed one
  by one).

## Related Docs
- `.github/workflows/test.yml` (`frontend` job: `npm ci`, `npx vitest run`, `npm run build`, Node 24).
- `docker/frontend.Dockerfile` (node:24.21.0 builder).

## Related Stored Artifacts
- None.

## Related Code Areas
- `frontend/package.json`, `frontend/package-lock.json`.
- `frontend/eslint.config.js`, `frontend/vite.config.ts`, and the 12 `frontend/src` files that import
  `lucide-react`. Change these only with a go.

## Assumptions / Open Questions
- The peer and engine requirements above come from `npm view` on 2026-10-25. Re-check them at the version you
  install.
- If lint already fails on main before any move, record that baseline and compare against it.

## Implementation Notes
- #570 lucide-react ^0.563.0 -> ^1.61.0 (landed): `tsc -b` clean, so no alias was dropped. lucide 1.x ships `dist/esm/icons/*.mjs`, so `iconScene.test.ts:102` now reads `${name}.mjs` instead of `${name}.js` (a change to how the test finds the file, not to what it asserts; `LUCIDE_PATHS` untouched). Bundle 338.40 -> 341.76 kB. vitest 369/369, build ok, lint identical to the 21-problem baseline.
- #569 eslint ^9.39.1 -> ^10.13.0 (landed, own commit): peer bumps `@eslint/js` ^10.0.1, `eslint-plugin-react-hooks` ^7.1.1, `typescript-eslint` ^8.72.0 (all in-major; the old lockfile versions rejected eslint 10 and `npm run lint` stopped with ELSPROBLEMS). vitest 369/369, build ok, audit 0. No `frontend/src` or config change; `eslint.config.js` runs unchanged.
  Lint: 21 problems before (18 errors, 3 warnings) and 21 after (17 errors, 4 warnings), but the mix changed because react-hooks 7.1.1 reports differently. Nothing is fixed in this PR; list for the next lint cleanup:
  - Dropped (errors): `react-hooks/preserve-manual-memoization` at `src/App.tsx:16:43` and `src/App.tsx:28:42`.
  - New (error): `react-hooks/refs` at `src/hooks/useCanvas.ts:40:3` (rule count 10 -> 11).
  - New (warning): `Unused eslint-disable directive` (for `react-hooks/set-state-in-effect`) at `src/visualAssets/MapHarness.tsx:61:5`.
- #568 vitest ^4.1.12 -> ^5.0.5 (landed, own commit): vite 7 is inside vitest 5's peer range, @types/node is fine, audit 0. Cause of the one source change: `src/test/setup.ts` imported `@testing-library/jest-dom`, which only brings the jest typings; vitest 5 no longer picks them up for its `Assertion` type, so `tsc -b` failed with 24 TS2339 errors (`toBeInTheDocument`, `toHaveStyle`, `toHaveAttribute`) in four test files. The line now reads `import '@testing-library/jest-dom/vitest'`, jest-dom's documented vitest entry (registers the same matchers on vitest's `expect` and supplies the `declare module 'vitest'` typings). Assertions unchanged. After: `tsc -b` 0 errors, build ok, vitest 31 files / 369 tests, lint identical to the state after #569.
- #567 @vitejs/plugin-react ^5.1.1 -> ^6.1.2 with vite ^7.3.7 -> ^8.3.5 (landed, own commit; version bumps only): `@tailwindcss/vite` ^4.1.18 -> ^4.3.3 is the strictly required peer (4.1.18 peers vite up to 7, so `npm install` failed with ERESOLVE; 4.2.2 was the first release accepting vite 8); the lockfile moves tailwindcss to 4.3.3 with it. `npm ls` clean, audit 0, build ok (bundle 341.76 -> 340.50 kB, CSS 33.20 -> 33.66 kB, build time about 3.5s -> 1.8s), vitest 31 files / 369 tests, lint identical to the state after #569. `npx vite build -c vite.rehearsal-bundle.config.ts` (the asset bundle capture build, no Playwright) also builds on vite 8; `e2e-artifacts/rehearsal-bundle` was deleted afterwards.
- Known vite 8 notice, left alone (no config edit in this PR): both the build and vitest print `vite.config.ts:10:25` uses `__dirname`, unsupported by `configLoader: 'native'`, which is planned to become the default in a future Vite major. `import.meta.dirname` fixes it. The rehearsal-bundle build prints the same notice.
- Decisions: #570 landed (53f1cfb59), #569 landed (b23c2ffd1), #568 landed (9557746d5), #567 landed (cd0341276). All four dependabot PRs are closed as "landed" after the merge.

## Test Summary
- After each move, under Node 24: lucide 1.61 (vitest 369/369 after the `.mjs` test fix, build ok, lint 21 problems unchanged); eslint 10 (vitest 369/369, build ok, lint 21 problems with a changed mix, see Implementation Notes); vitest 5 (`tsc -b` 0 errors after the jest-dom/vitest import, vitest 369/369, lint unchanged); plugin-react 6 + vite 8 (build ok, vitest 369/369, lint unchanged, `npm audit` 0, rehearsal-bundle build ok).

## Files Changed
- frontend/package.json, frontend/package-lock.json
- frontend/src/visualAssets/__tests__/iconScene.test.ts (`.js` -> `.mjs`), frontend/src/test/setup.ts (jest-dom/vitest entry)

## Completion Summary
All four majors landed as one commit each (53f1cfb59, b23c2ffd1, 9557746d5, cd0341276), each on rpg-planner-ubuntu's go; two one-line test-side edits, no config edits. The dependabot PRs #567 to #570 are closed as landed after the merge.
