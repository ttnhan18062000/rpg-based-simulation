---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-05
tags: [planning, delivery]
---
# Handover — codebase-planner
Updated: 2026-10-05 ~15:00Z (#351 and #329 both MERGED; closure batch handed to the implementer; safe to /clear)

**On another machine:** pull main, copy `docs/plans/codebase_health/handoffs/session/*.md` into `.claude/handover/`; lines marked "(this machine)" describe the original VM only.

## Open
- **#329 MERGED EARLY by the owner** 2026-10-05T14:47Z (squash c8c355459, head c7086195e), not on the planned 10-18. The gates are blocking on main: ratchet, mypy, package registry, ast-grep N3/N4/E3. jscpd and Import contracts stay report-only. Main's soak debt (27 ratchet rows + 3 mypy entries, attribution in the soak review draft + handoff_to_rpg) was accepted before the merge, so main was green.
- **Owner step still open: required checks.** Ruleset 14220945 (`protect_branches`) had NO required status checks at merge. Main produced `Type check` (success) on c8c355459; `Code health` was in progress at ~15:00Z. Once it is green, the owner adds exactly `Code health` + `Type check`. Remind them if it isn't done.
- **Closure batch owed ("gates-flip-closure")**, handed to codebase-implementer 2026-10-05: new branch/worktree from main; finalize both soak reviews (window CUT SHORT to about 2 days, by the owner's decision); closure tool per FLIP-BLOCKING ticket (since #350 it deletes the todos/inprogress copies itself); gates epic + `todos/python-code-craft-gates/` to done by hand; handoff updates ("gates blocking since 2026-10-05") to rpg/testing/agent-working; the #329 squash title wrongly says "merge on or after 2026-10-18" (note it, don't rewrite). Review each commit; owner yes for push/PR/merge.
- **#351 MERGED** 2026-10-05T13:40Z (e9585eb02): import-linter advisory, 17 contracts. Soak ends 2026-10-19T13:40Z → `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (BLOCKED, todos/python-code-craft-structure/, testing's 4 conditions in its Assumptions) earliest 10-19. phase19's kernel.py imports wait on rpg. knowledge-index-update owed (OOM at the 2 GB cap).
- Notices sent 2026-10-05: perf-planner and asset-planner told the gates are blocking. rpg/testing/agent-working get it via the closure PR's handoffs.
- Filed: `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT` (P3; the 2 local 60 s failures + the test_edit_ratchet_hook load flake). Frontend flake `useSimulation.test.tsx:152` passed to testing as an FYI.
- Pending user decisions: required checks (above). Owner-only, not yet raised: reopening `src/` for M7; the codebase-seat diff of `session_authority.yaml`.

## Dated next steps
- 2026-10-10: by-hand check of main's `Code health` / `Type check` annotations (now blocking, so read failures on PRs too) and of the code-scanning runs.
- 2026-10-19 ≥ 13:40Z: import-linter flip ticket (soak review, owner makes it required, retire class E tests per testing's conditions).

## For the owner (not tickets)
- Main checkout is behind origin/main, with 2 dirty W40 tools shards (`main.tools.jsonl`, `python-code-craft-agent-integration.tools.jsonl`): on the next sync commit or move the extra lines; never a plain reset.
- `data/runs/` cleanup undone; local clutter: untracked `src/social/`, `src/graphify-out/`, root `agent-monitoring/`, `reviews/`, `stored_artifacts/`; `graphify-out/graph.json` stale (rebuild OOMs at 2 GB).
- Follow-up noted in #329's body: `actions/setup-node@v4` Node 20 deprecation (frontend job shares it).

## Blocked codebase tickets
- `todos/python-code-craft-structure/TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (soak until 2026-10-19T13:40Z; phase19 part waits on rpg's kernel.py decision).
- `todos/codebase-domain-root/TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC` (scope-only).
- M7 refactor lane deferred while `src/` is frozen (debt: ~3,724 registry rows, 1,569 mypy baseline).

## Review checklist (lessons)
- Advisory jobs are always green: read summaries / `gh api .../check-runs/<id>/annotations` and the code-scanning runs.
- New tests must pass `tests/tools/test_*guard*.py`; compare pass/skip totals with main.
- A live-repo completeness test in a blocking lane makes the rule blocking.
- Dependency added to a group: re-run the `tests/static` pin tests.
- A REGISTRY-only CONFLICTING PR runs no workflows: merge main locally, push.
- A PR adding any `src/` file trips the `scope_files` pin until agent-working changes it: read every failing job.
- A subprocess timeout doesn't bound npx grandchildren: keep a job `timeout-minutes` backstop.
- Ask the implementer to run `git status -sb` before every push question.

## Pointers
- Briefs on main: `docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md`, `import_linter_adoption_ticket_brief.md`. Implementer's closure brief: `.claude/handover/codebase-implementer.md`.
- Roadmap `docs/plans/codebase_health/python_code_craft_roadmap.md`; handoffs `docs/plans/codebase_health/handoffs/`.
- Implementer handover: `.claude/handover/codebase-implementer.md`.
