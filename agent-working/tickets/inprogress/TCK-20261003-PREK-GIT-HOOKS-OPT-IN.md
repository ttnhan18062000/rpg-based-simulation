---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PREK-GIT-HOOKS-OPT-IN
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-PREK-GIT-HOOKS-OPT-IN

## Title
M4d: prek git hooks with an opt-in install that keeps the post-commit reindex hook

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Roadmap 6.2 picks prek as the git hook runner. `.git/hooks` is shared by every worktree on this machine, so owner decision 2026-10-03: install is opt-in only. `make install-hooks` today copies tools/hooks/post-commit-reindex.sh into .git/hooks/post-commit; prek must not overwrite it.

## Scope
- `.pre-commit-config.yaml` run by prek (pinned): ruff check on staged `.py` files filtered through the ratchet so only new violations block the commit; `uv lock --check` when pyproject.toml or uv.lock is staged
- An opt-in Makefile target that installs prek's pre-commit hook and the existing post-commit reindex hook together; neither overwrites the other; idempotent
- Document install, bypass (`--no-verify`) policy and uninstall in docs/guidelines/agent_working_environment.md
- Tests: the target's recipe and the config's hook list (static), and the ratchet filter on a staged-file list

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- Installing hooks automatically from any make target, script, CI step or session hook
- Formatting hooks (decision 8.3)

## Acceptance Criteria
- [ ] Opt-in target installs both hooks; running it twice is a no-op; existing post-commit behaviour unchanged (demonstrated in a scratch clone, not the shared .git)
- [ ] A commit adding a new ruff violation in a staged file is rejected with the ratchet's message; a commit touching only grandfathered code passes
- [ ] Hook run time on a typical one-file commit recorded and under 5 s
- [ ] No target, script or CI step installs hooks implicitly (static test)
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB (depends on: reseeded registry)

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None.

## Related Code Areas
- .pre-commit-config.yaml (new)
- Makefile (install-hooks)
- tools/hooks/
- tools/code_health/

## Assumptions / Open Questions
- Verification must use a scratch clone: installing into this machine's shared .git/hooks affects every session
- prek version and whether it is a Python dependency (lock group) or a standalone binary is for Investigate

## Implementation Notes
- Dependency: `prek==0.5.4` in the `dev` group (planner: yes, because the installer tests sort into `tools-f-z`/`tools-a-e` and must have the binary; a skip there would hide a broken install). The `uv.lock` diff adds exactly one package, `prek` 0.5.4 (18 lines, wheels only, no dependencies); `requirements.txt` gains one line; `uv lock --check` passes.
- `tools/code_health/staged_ratchet.py` (planner condition D, reuse): keeps existing safe `src/**/*.py` paths with `sarif_feedback.changed_python_files`, runs `ruff check --output-format json` on them, converts with `adapters.adapt_ruff` and compares with the registry rows of those files through `ratchet.compare`; it prints `ratchet.format_report` of the NEW / WORSE entries and a how-to line. Nothing re-implements the grouping.
- Planner condition A (worktrees without the environment must not be blocked): `.git/hooks` is shared by every worktree, so both hooks skip with one visible line and exit 0 where they cannot run. `tools/hooks/code_health_pre_commit.sh` prints "code-health hook skipped: environment not synced (uv sync) or tools.code_health not importable here" when `python3` cannot import the module; the module itself skips (exit 0, "code-health hook skipped: <reason>") when ruff is not installed for that Python, the registry is missing, or the registry/ruff output is unreadable; `tools/hooks/uv_lock_pre_commit.sh` skips when `uv` is absent. Only a real NEW or WORSE result (or a stale `uv.lock`) blocks. prek hides the output of a passing hook, so both hooks have `verbose: true` (found by a test: the skip line was invisible without it). Tested in a temporary repo whose staged deletion of `tools/code_health` makes the module unimportable (commit succeeds, skip line shown) and in unit tests (no ruff, no registry, unusable registry).
- Planner condition B (no network in the hook): `uv lock --check --offline` works from the lockfile alone: 0.07 s on the current tree, exit 0 even with `HTTPS_PROXY` pointing at a dead port, and exit 1 on a deliberately stale `pyproject.toml`. The hook uses that form; the uv-lock hook is kept (not dropped). CI already runs `uv sync --locked`.
- Planner condition C (staged content): the scratch-clone demonstration shows prek printing "Unstaged changes detected. Temporarily saving them to ..." and "Restored unstaged changes ...": a file with a new ruff violation only in its unstaged part commits (exit 0) and the unstaged violation is still in the working tree afterwards. Also a pytest (`test_the_hook_checks_the_staged_content_not_the_working_tree`).
- Installer `tools/hooks/install_git_hooks.py` + `make install-prek-hooks` / `make uninstall-prek-hooks` (help text: OPT-IN, affects EVERY worktree). Resolves the hooks directory with `git rev-parse --path-format=absolute --git-path hooks` (the shared common directory; a test installs from a worktree and finds the hook in the main repo's directory). `post-commit`: installed only when absent; byte-identical -> unchanged; different -> kept and reported. `pre-commit`: `prek install --hook-type pre-commit` (a foreign hook becomes `pre-commit.legacy` and still runs, tested); already-prek -> unchanged. Uninstall removes only the prek shim (restoring a legacy hook) and a post-commit identical to ours; `post-merge` and every other hook untouched (tested). The older `make install-hooks` (which `cp`-overwrites post-commit) is left unchanged (planner: out of scope); the guide says which to use.
- **Review fix (planner, Important): prek's own shim ran before the hook scripts' skip logic and could block other worktrees.** Reproduced two cases with prek 0.5.4 (and kept as control tests): (1) no `.pre-commit-config.yaml` in the checked-out tree: prek's default install exits 1 ("No `prek.toml` or `.pre-commit-config.yaml` found") for every commit on a branch cut before this PR; (2) prek not resolvable: the shim hard-codes the `.venv/bin/prek` it was installed with, falls back to `PATH`, then `exec prek` fails ("not found", exit 1) machine-wide whenever the main `.venv` is re-synced without prek or deleted. Fix in `tools/hooks/install_git_hooks.py`: (1) install with `--allow-missing-config` (the shim then passes `--skip-on-missing-config`); (2) after prek writes its own shim, the installer inserts a small guard before the final `exec` (marker `# guard added by tools/hooks/install_git_hooks.py`): without a runnable prek it prints `pre-commit hook skipped: prek not found (project environment not synced: uv sync)` and exits 0. The shim keeps prek's own header and id, so `prek uninstall` still removes it (tested); an older unguarded shim is upgraded in place by re-running install (tested, and idempotent); a new `--prek PATH` option lets tests install with a removable copy. Tests with real commits in temporary repositories: no config -> commit succeeds; prek removed and not on PATH -> commit succeeds with the visible skip line; control tests show prek's unguarded shim does exit non-zero in both cases (so the new tests discriminate); a new violation still blocks when config and prek are both present. The guide's note on what install does to other worktrees is updated. Verified only in temporary repositories (the shared `.git/hooks` was not touched; it still holds only `post-merge`).
- Planner nit, taken: when `guard_shim` does not recognise prek's shim (a future prek format change), prek has already written its unguarded shim. The installer now runs the same `prek uninstall` removal before re-raising, so a failed install leaves no blocking shim behind; test with a fake prek that writes an unknown shim format (`test_an_unrecognised_shim_format_is_removed_again_instead_of_left_unguarded`).
- Docs: new section "Git hooks (opt-in)" in `docs/guidelines/agent_working_environment.md` (what they check, that install affects all worktrees on the machine, never-overwrite behaviour, `install-hooks` overwrites and `install-prek-hooks` does not, `--no-verify` policy, uninstall, verify only in a scratch clone) and one line in `python_code_standard.md`.
- Scratch-clone demonstration (`git clone --no-hardlinks` of this repo, real registry, real `src/engine/kernel.py`, installer run with `--repo <clone>`): install #1 creates `pre-commit` and `post-commit`; install #2 leaves both files byte-identical; `post-commit` is byte-identical to `tools/hooks/post-commit-reindex.sh`. (A) staging a new bare `except` in `kernel.py`: the commit is rejected with "NEW violations (no baseline row) (1): src/engine/kernel.py:1421 [ruff E722] value=1 ... FAIL: 1 new, 0 worse" and the how-to line, 0.64 s end to end. (B) a comment-only change to the same file (154 grandfathered findings): passes, one-file commit 0.61 s (hook 0.40 s). (C) as above. (D) staging `pyproject.toml`: `uv-lock-check` passes in 0.17 s (commit 0.39 s); with no pyproject staged it is skipped. All well under the 5 s target.
- **Process incident, recorded plainly.** While setting up that demonstration I ran a chained shell command in which `git clone --local` failed (hardlinks across devices) and the following `cd` was skipped by the `&&` chain, so the following commands ran in the REAL repository: `git add -A` + `git commit --no-verify` created an unintended local commit (`f5b1d6c1`, 40 files, including old-root residue) on `python-code-craft-gates`, and the installer installed `pre-commit` and `post-commit` into this machine's shared `.git/hooks` (for about a minute; any commit by another session in that window would have run them). Nothing was pushed. Reverted at once: `python3 tools/hooks/install_git_hooks.py uninstall` (the shared directory is back to only `post-merge`, whose checksum is unchanged, no `.legacy` files) and `git reset HEAD~1` of my own unpushed commit (HEAD back at `7b2d61f6`, nothing staged, all changes intact; the commit is still in the reflog). The demonstration was then rerun as a script with `set -euo pipefail`, `git clone --no-hardlinks` and a guard that aborts unless the repository root is the scratch clone before every step; it ran clean and the real repository's hooks and HEAD were unchanged afterwards (checked). Reported to the planner.

## Test Summary

## Files Changed
`pyproject.toml` (`prek` in `dev`), `uv.lock`, `requirements.txt` (generated), `.pre-commit-config.yaml` (new), `tools/code_health/staged_ratchet.py` (new), `tools/hooks/install_git_hooks.py` (new), `tools/hooks/code_health_pre_commit.sh` (new), `tools/hooks/uv_lock_pre_commit.sh` (new), `Makefile` (`install-prek-hooks`, `uninstall-prek-hooks`; the `install-hooks` help text now says it overwrites), `docs/guidelines/agent_working_environment.md`, `docs/guidelines/python_code_standard.md`, `docs/REGISTRY.yaml`. Tests (all new, no existing test edited): `tests/tools/test_code_health_staged_ratchet.py` (9) and `tests/tools/test_code_health_install_git_hooks.py` (15, including the static opt-in guards and real commits through prek in temporary repositories).

## Completion Summary
