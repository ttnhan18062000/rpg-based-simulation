---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-05
tags: [planning, delivery]
---

# Handover — codebase-implementer
Updated: 2026-10-05 (new batch `import-linter-adoption` started; #329 parked until 2026-10-18)

## Open
- **On another machine:** fetch `import-linter-adoption`, copy `docs/plans/codebase_health/handoffs/session/*.md` back to `.claude/handover/` (the committed copies mark machine-specific lines with "(this machine)"; ignore or redo those).
- **Batch A (current): `import-linter-adoption`**, branch `import-linter-adoption` from `origin/main`, worktree `/home/vboxuser/Work/rpg-import-linter` (this machine). Brief: `docs/plans/codebase_health/import_linter_adoption_ticket_brief.md` (ignored copy: `.claude/handover/next-batch/import_linter_adoption_ticket_brief.md`). Owner yes 2026-10-04: import-linter advisory, accept the 20 `src.<pkg>` root entries, no `src/` diff. This batch retires NO test (testing condition 1); phase19's 5 `kernel.py` function-local imports sit in `ignore_imports` pending rpg. Tickets: `TCK-20261004-IMPORT-LINTER-ADOPTION` (rescoped OPEN), `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (BLOCKED, follow-up, listed in the structure `SEQUENCE.md`). One PR for the batch including the planning commit; send each ticket commit to `codebase-planner` for review.
- **Push rule:** the owner's instruction covers pushes of THIS branch that carry the handover copies (re-copy both handover files at every push). It does NOT cover opening the PR, any merge, or any push to #329: ask via AskUserQuestion after `git status -sb` + `git ls-remote`.
- **Batch B (parked): PR #329** `python-code-craft-gates-flip` (worktree `/home/vboxuser/Work/rpg-code-craft`, this machine). Remote head `434000a3b`; CI green on `8b0865cf7`; CONFLICTING (REGISTRY.yaml) so it runs no workflows until `origin/main` is merged on merge day. Do NOT merge before **2026-10-18 05:00Z (12:00 local, +07)**. Leave that worktree untouched. Tickets (all `inprogress/` on that branch, standard): `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`, `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING`, `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING`.
- **Do not write any closure record early** for batch B (`record_hand_orchestrated_closure.py`, working_log row, ticket moves, `done_checker_static`, epic/folder move): they stamp dates, and the working_log tool refuses a second row.
- Conflicts with #329 expected for this batch: `.github/workflows/test.yml`, roadmap, `agent_working_environment.md`, `pyproject.toml`?, and the adoption ticket file. Tell the planner which files conflict before resolving anything.
- Main checkout (this machine) has two modified W40 shards (`main.tools.jsonl`, `python-code-craft-agent-integration.tools.jsonl`): rows already on main, do not reset them. The pre-push hook notes them on every push; it is about the main checkout, not the PR.

## Merge day for #329 (2026-10-18 at or after 05:00Z), one sitting with the owner
1. `git fetch origin`; if #329 shows CONFLICTING (REGISTRY.yaml, expected), `git merge origin/main` in the #329 worktree (the merge driver regenerates it), re-check `git diff origin/main...HEAD --name-only | grep '^src/'` is empty.
2. Precondition on the merged tree, record both runs in `python_code_craft_structure_soak_review.md`: `python3 -m codebase.health check` (0 new/worse incl. ast_grep), `python3 -m codebase.structure.packages validate`, `python3 -m codebase.gates.mypy_gate`. Findings go to the owning domain or become reviewed rows with that domain's reason, never a silent reseed.
3. Finalize the soak reviews (`gh run list` + check-run annotations: runs, exit-1 runs, exit-2 runs, new/worse findings with disposition, reseeds, baseline syncs, reviewed rows; M5: per-rule N3/N4/E3 real vs false positive, Package registry problems). Ratchet window ends 2026-10-17, mypy and M5 windows 2026-10-18T04:59Z. A false-positive class stops the flip and goes to the planner.
4. Closure commit (ask the owner before pushing): `record_hand_orchestrated_closure.py` per ticket (`--title`, `--log-summary`, never `--agent <session-name>`; it appends the working_log row itself), `done_checker_static.py`, `mechanism_registry_changed_code_check.py`; move the three tickets to `done/` and staging artifacts to `stored_artifacts/`; closing ticket 1 closes `TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC` and moves `todos/python-code-craft-gates/` to `done/`; the structure folder stays open (import-linter flip). Update roadmap Section 8 and stage `agent-working/agent-monitoring/` shards. Regenerate `docs/REGISTRY.yaml`. Push, CI green.
5. Owner adds exactly `Code health` and `Type check` as required checks in the `main` ruleset, then `gh pr checks 329 --required` lists both (record date and who in ticket 1), then merge with `--admin --match-head-commit` after the owner's yes.
6. After merge the planner announces to every planner.
Tell the planner the result of each step. Before every push/merge: `git status -sb` + `git ls-remote`, then a direct AskUserQuestion that matches what is unpushed.

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
