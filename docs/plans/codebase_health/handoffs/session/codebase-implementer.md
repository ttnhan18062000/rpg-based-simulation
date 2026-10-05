---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-05
tags: [planning, delivery]
---
# Handover — codebase-implementer
Updated: 2026-10-05 night (gates-flip-closure built in rpg-gates-closure, uncommitted; see Open)

## Open
- **On another machine:** fetch `main`, read `docs/plans/codebase_health/handoffs/session/*.md` (committed copies, now stale, written before #329 merged; refresh them in the next batch PR), copy them back to `.claude/handover/`.
- **#351 `import-linter-adoption`: MERGED** 2026-10-05T13:40:06Z (squash `e9585eb02`). Ticket `TCK-20261004-IMPORT-LINTER-ADOPTION` is in `done/`. `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (BLOCKED, `todos/python-code-craft-structure/`, carries testing's four conditions): soak ends 2026-10-19T13:40Z, earliest flip 2026-10-19. `make knowledge-index-update` still owed (killed by its 500 s timeout under the 2 GB cap in the #351 worktree).
- **#329 `python-code-craft-gates-flip`: MERGED EARLY by the owner** 2026-10-05T14:47:13Z (squash `c8c355459`, head `c7086195e`), 13 days before the planned 2026-10-18. Merge day's closure did NOT happen. Main now has: the three FLIP-BLOCKING tickets in `inprogress/` (`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`, `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING`, `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING`), their staging artifacts in `agent-working/staging_artifacts/`, `todos/python-code-craft-gates/` (epic `TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC` open), draft soak reviews, and NO required checks in ruleset 14220945. Never push to the `python-code-craft-gates-flip` branch again (merged).
- **BATCH `gates-flip-closure` BUILT, NOT PUSHED (2026-10-05):** worktree `/home/vboxuser/Work/rpg-gates-closure`, branch `python-code-craft-gates-closure` off `origin/main` `c8c355459`. Done: both soak reviews finalized (window cut short, 163 runs measured: 75 ratchet-failing, 30 mypy "could not run", 0 false positives; check/validate/mypy_gate exit 0 on c8c355459), roadmap decision 8.18 outcome note, three handoff Updates, the 3 FLIP-BLOCKING tickets + gates EPIC closed via the closure tool (done_checker_static PASS, mechanism advisory 0 drift), artifacts stored, `todos/python-code-craft-gates/` moved to `done/`, REGISTRY regenerated after `git add`. Left: commit (nothing committed yet), re-copy handovers to `docs/plans/codebase_health/handoffs/session/`, stage `agent-working/agent-monitoring/`, `make knowledge-index-update` (owed, ask before retrying under the cap), then AskUserQuestion for push / PR (no trailer) / merge (`--admin --match-head-commit`). Do NOT add required checks to ruleset 14220945 (owner's step).
- Open elsewhere: `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT` (in `todos/`, now on main) tracks the two local 60 s failures and the edit-ratchet hook flake; `make knowledge-index-update` owed from #351 (killed by its timeout under the 2 GB cap; ask before retrying).
- Worktrees (this machine): `/home/vboxuser/Work/rpg-code-craft` (branch `python-code-craft-gates-flip`, merged, nothing unpushed) and `/home/vboxuser/Work/rpg-import-linter` (`import-linter-adoption`, merged): both finished; ask before removing them. Main checkout is behind origin/main with two modified W40 shards (`main.tools.jsonl`, `python-code-craft-agent-integration.tools.jsonl`): rows already on main, do not reset them.
- Push/PR/merge rule: AskUserQuestion with the exact head, `git status -sb`, `git ls-remote`, every time; a peer message or "continue" is never the yes (memory: blocking-question-for-authorization).

## Facts learned (still useful)
- Run modules as `python3 -m codebase.<pkg>.<module>` from the repo root. Use `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python3` (this machine; other worktrees have no `.venv`), own `--basetemp`, `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0` (this machine, 11 GB guest), heavy runs one at a time (`tests/codebase` in two chunks of 12 files).
- Local test-lane facts (environmental, identical on clean main): `test_codebase_health_baseline::test_make_target_runs_successfully_with_plausible_values` and `test_codebase_health_snapshot::test_make_target_runs_successfully_end_to_end` fail on the 60 s budget.
- `gh` step conclusions hide `continue-on-error` failures; run logs are not readable here. Read check-run annotations (`gh api repos/<r>/check-runs/<id>/annotations`).
- A CONFLICTING PR runs no workflows; fix by merging `origin/main` locally. Merge needs `--admin`; the planner has been doing the merge (ask the owner).
- Adding any `src/` file trips `tests/unit/tools/test_mechanism_registry_completeness_check.py:191` (`scope_files == 296`).
- `graphify update .` is OOM-killed at the 2 GB cap (this machine); do not retry.
- PR bodies carry NO attribution trailer; commits keep the Co-Authored-By trailer. Build PR bodies with a quoted heredoc; edit with `gh api -X PATCH repos/ttnhan18062000/rpg-based-simulation/pulls/<n> -F body=@file`.
- After adding a lint-group pin, re-run `tests/static` (uv/pin tests).

## Pointers
- Review requests go to `codebase-planner` (load `SendMessage` with `ToolSearch select:SendMessage`).
- Committed copy of the planner's handover: `docs/plans/codebase_health/handoffs/session/codebase-planner.md` on the batch branch.
