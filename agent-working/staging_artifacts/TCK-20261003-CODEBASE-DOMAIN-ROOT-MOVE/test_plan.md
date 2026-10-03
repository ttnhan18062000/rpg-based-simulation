---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE
artifact_type: test_plan
tags: [architecture, delivery]
---

# Test Plan — TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE

Scoped runs only, one heavy command at a time under the memory cap.

- Moved tests pass from `tests/codebase/` unchanged except paths/imports (normal flow, same assertions, so behaviour parity is proven by the existing suite).
- New guard tests (`tests/codebase/test_domain_root_layout.py`): fails if `tools/code_health/` or any of the five flat files reappear (failure mode); `codebase` resolves inside the repo (shadowing); every moved module imports under its new name; installer idempotent re-install over an existing prek shim and clean uninstall (edge); orphan check classifies `codebase/**` files (regression).
- Static/CI: `tests/static`, `tests/tools/test_ci_workflow_test_coverage.py`, `tests/tools/test_ci_split_tools_jobs.py`, `tests/tools/test_tools_orphan_check.py`, the edited `test_ci_uv_install.py` and `test_typecheck_gate_configured.py`.
- Command-level: `python3 -m codebase.health check` reports 0 new / 3,617 unchanged; `make typecheck-py` reports 0 new; `make codebase-health-baseline` and snapshot targets run; `make install-prek-hooks` in a guarded `--no-hardlinks` clone only.
- Docs: `validate_frontmatter`, docs tests under `tests/docs`, `make docs-registry`.
- Final `git grep` acceptance check and `git diff --stat` shows no `src/`, `.claude/`, `CLAUDE.md`.
