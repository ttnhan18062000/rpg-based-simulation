---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES
phase: open
date: 2026-10-25
tags: [security]
---

# TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES

## Title
Decide each open frontend major-version Dependabot PR (#567, #568, #569, #570) one at a time, landing the ones that pass build, tests and lint

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner direction 2026-10-25, Lane U1 (#715 issuecomment-6393397119). The owner wants major moves reviewed one by one,
and one superseding PR, with each dependabot PR closed and a reason given. Four major-version dependabot PRs are open
on `frontend/`:

| PR | move | scope | what the 2026-10-25 check found |
|---|---|---|---|
| #570 | lucide-react 0.563 → 1.55 | **runtime** (ships in the bundle) | Peers on React 16-19 are fine. 12 files under `frontend/src` import 32 icons, among them `Home` and `BarChart3`, which are older alias names. 1.0 may have dropped aliases, and `tsc -b` in `npm run build` catches a missing export. |
| #569 | eslint 9.39 → 10.12 | dev | `frontend/eslint.config.js` is already a flat config. typescript-eslint and eslint-plugin-react-hooks latest accept eslint 10. Check `eslint-plugin-react-refresh` and `@eslint/js`. |
| #568 | vitest 4.0 → 5.0.3 | dev | Peers accept vite 7. It needs Node ^22.12 or 24 (CI and the image are on 24). Not needed for security: the critical alert is fixed in 4.1.0, which the refresh ticket handles. |
| #567 | @vitejs/plugin-react 5.1 → 6.1.2 | dev | **Needs vite ^8.0.0**, so it brings a vite 7 → 8 major (Rolldown) that no dependabot PR proposes. |

## Scope
Do this after `TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH`, on the same branch. Take the moves one at a time,
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
- [ ] Each of #567, #568, #569 and #570 has a recorded decision in this ticket: landed (with its commit), or parked
      (with its reason).
- [ ] Each landed move is its own commit, and after it `npx vitest run`, `npm run build` and `npm run lint` pass
      under Node 24, with lint no worse than before.
- [ ] No `frontend/src/**` or config change lands without rpg-planner-ubuntu's go for that move.
- [ ] After the superseding PR exists, each dependabot PR is closed with a comment that gives its decision and points
      to the PR. For a parked move, the comment says what would unblock it.
- [ ] No new Dependabot alert opens on `frontend/package-lock.json` because of a landed move.

## Related Tickets
- `TCK-20261025-FRONTEND-LOCKFILE-SECURITY-REFRESH`: done first, same PR.
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

## Test Summary

## Files Changed

## Completion Summary
