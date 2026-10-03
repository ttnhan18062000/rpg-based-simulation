---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-PREK-GIT-HOOKS-OPT-IN
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261003-PREK-GIT-HOOKS-OPT-IN

Same branch (`python-code-craft-gates`), after ticket 3. No `src/`, `.claude/`, `CLAUDE.md` edits; nothing is installed into this machine's shared `.git/hooks`.

1. **Dependency**: `prek==0.5.4` in `dev`; `uv lock --system-certs` (diff must be prek only; list added packages); regenerate `requirements.txt`.
2. **`tools/code_health/staged_ratchet.py`**: `python3 -m tools.code_health.staged_ratchet FILES...` keeps existing safe `src/**/*.py` paths, runs `ruff check` (json) on them, compares per ratchet unit with the registry rows of those files only, prints `ratchet.format_report` of the NEW / WORSE entries and a one-line how-to (fix it; `git commit --no-verify` policy in the guide), exits 1 on new or worse, 2 if ruff or the registry is unusable (with the reason), 0 otherwise or with no matching files.
3. **`.pre-commit-config.yaml`** (prek, `minimum_prek_version: 0.5.4`): repo `local`, `language: system`, two hooks: `code-health-ratchet` (`python3 -m tools.code_health.staged_ratchet`, `files: ^src/.*\.py$`) and `uv-lock-check` (`uv lock --check`, `files: ^(pyproject\.toml|uv\.lock)$`, `pass_filenames: false`). No formatter hooks (decision 8.3).
4. **`tools/hooks/install_git_hooks.py` + Makefile targets**: `make install-prek-hooks` and `make uninstall-prek-hooks`, help text says opt-in and machine-shared. Install: post-commit only if absent (identical -> no-op, different -> kept, said so, never overwritten), then `prek install --hook-type pre-commit` (foreign hook kept as `pre-commit.legacy`, prek's own behaviour); a second run is a no-op. Uninstall: `prek uninstall --hook-type pre-commit` (restores the legacy hook) and removes post-commit only if byte-identical to ours; `post-merge` and every other hook are never touched. The hooks directory is resolved with `git rev-parse --path-format=absolute --git-path hooks`, so worktrees work.
5. **Tests**: static (config hook list and entries, Makefile target recipes, no implicit install: no other target, script, CI step or `.claude` hook configuration references the install targets or `prek install`, `install`/`install-py` do not depend on them); unit (`staged_ratchet`: grandfathered passes, new violation rejected with the ratchet message, worse-than-row rejected, no files, tool unusable); integration in temporary git repos with the real prek binary (fresh install creates both hooks; second run changes nothing; a different existing post-commit is kept; a foreign pre-commit is kept as legacy and still runs; uninstall restores; `post-merge` untouched; a real commit with a staged new violation is rejected and one touching only grandfathered code passes).
6. **Scratch-clone demonstration** (recorded in the ticket): `git clone --local` of this repo into the scratchpad, run the installer there, commit a file with a new ruff violation (rejected with the ratchet's message), commit a grandfathered-only change (passes), time the hook on a one-file commit (target under 5 s), run install twice (no-op), check the post-commit behaviour unchanged, then delete the clone.
7. **Docs**: `docs/guidelines/agent_working_environment.md`: install (`make install-prek-hooks`, opt-in, machine-shared warning), what the hooks check, bypass policy (`git commit --no-verify` only with the owner's say-so or for a hotfix of the gate itself; never to hide a new violation), uninstall; `python_code_standard.md` one line.
8. **Close** in the batch closure commit after the green PR run.

## Scope guards
Nothing is installed automatically anywhere. No formatter. No check becomes blocking in CI. The existing `make install-hooks` is left as is (it is outside this ticket; the guide points to the new target for the pre-commit hook).

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| Opt-in target installs both hooks, twice is a no-op, post-commit unchanged, shown in a scratch clone | 4, 5, 6 |
| New ruff violation rejected with the ratchet's message; grandfathered-only commit passes | 2, 5, 6 |
| Hook time on a one-file commit recorded, under 5 s | 6 |
| No implicit install anywhere (static) | 5 |
| No src/.claude/CLAUDE.md in diff | scope guards |

## Questions for the planner
- `dev` group for prek (all CI jobs and the installer tests then have the binary), instead of `lint`?
- Leave `make install-hooks` (which overwrites post-commit) unchanged and only add the new non-overwriting target?
