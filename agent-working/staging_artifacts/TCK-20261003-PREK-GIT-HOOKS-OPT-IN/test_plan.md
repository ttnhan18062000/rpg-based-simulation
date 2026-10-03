---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-PREK-GIT-HOOKS-OPT-IN
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261003-PREK-GIT-HOOKS-OPT-IN

All runs one at a time under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`; exit status checked separately. Nothing touches the shared `.git/hooks`: every hook test uses a temporary git repository or a scratch clone.

- Unit (`staged_ratchet`): grandfathered group passes; no row -> NEW rejected with the ratchet message; above ceiling -> WORSE rejected; at ceiling passes; paths outside `src/` and unsafe paths ignored; no files -> 0; ruff unusable / bad registry -> 2 with the reason.
- Integration (real prek in temporary repos): fresh install (both hooks present and executable); second install changes no byte; a different existing post-commit is kept and reported; a foreign pre-commit is kept as `pre-commit.legacy` and still runs; uninstall restores the legacy hook and removes only our post-commit; `post-merge` and other hooks untouched; real `git commit` with a staged new violation fails with the ratchet's message, a grandfathered-only commit succeeds.
- Static: the config's hook ids, entries, `files` patterns and `minimum_prek_version`; Makefile targets call only the installer; no implicit install in any target, script, workflow or `.claude` hook configuration.
- Scratch clone (recorded): reject/accept flows, hook wall time on a one-file commit, idempotent installs, post-commit unchanged.
- Dependency: `uv lock --check`; export diff is the new line(s) only; `tests/static`, `test_generate_registry`, old-root guard.
