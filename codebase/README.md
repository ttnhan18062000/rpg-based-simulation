# codebase — Python code-craft tooling, gates, hooks, reports and baselines

The root folder of the **codebase domain** (owner: the codebase planner/implementer pair). It holds what the
domain owns and changes, so ownership is one glob. Decision record and the options that were weighed:
`docs/plans/codebase_health/codebase_domain_root.md`. Roadmap: `docs/plans/codebase_health/python_code_craft_roadmap.md`.
Standard the tools enforce: `docs/guidelines/python_code_standard.md`.

| Path | What | Run it |
|---|---|---|
| `health/` | ruff, complexipy, jscpd and line-count adapters, the ratchet, the exceptions registry, metrics | `python3 -m codebase.health check` (`make code-health`) |
| `gates/` | `mypy_gate` (baseline-filtered mypy), `sarif_feedback` (PR annotations and SARIF), `staged_ratchet` (the pre-commit hook's engine) | `python3 -m codebase.gates.<name>` |
| `hooks/` | prek hook scripts for the code-health ratchet and the uv.lock check, and the opt-in installer | `make install-prek-hooks` |
| `reports/` | health baseline, snapshot and scorecard, impact, PR impact, unreachable-code audit | `python3 -m codebase.reports.<name>` (Makefile targets keep their names) |
| `baselines/` | `code_health_exceptions.jsonl` (the grandfathered violations), `mypy_baseline.txt` | reseed only on main, see the standard |
| `config/` | `.jscpd.json` | read by `health/scan.py` and `make code-health` |

Tests: `tests/codebase/`, collected by the `tools-a-e` CI job (it installs the lint group, so the tool-dependent tests run
instead of skipping).

## Rules

- Run modules with `python3 -m codebase.<pkg>.<module>` from the repository root. A path invocation
  (`python3 codebase/reports/x.py`) puts the wrong directory on `sys.path` and the package imports fail.
- Direction: `codebase` may import `tools` (for example `tools.agent_working_paths`); `tools` must never import `codebase`
  (guarded by `tests/codebase/test_domain_root_layout.py`).
- No behaviour of a tool changes by moving it here; change behaviour in its own ticket.

## What lives elsewhere, and why

- `pyproject.toml` (ruff, complexipy, mypy, `[tool.mypy_baseline]`) and `.pre-commit-config.yaml`: the tools read them from
  the repository root.
- `agent-working/agent-monitoring/codebase_health_history.jsonl`: snapshot history, in agent-working's data root until that
  domain agrees to move it. The snapshot keeps writing there.
- `tools/hooks/post-commit-reindex.sh`, `registry_post_merge_regen.sh`: agent-working's hooks.
- Cross-domain registries in `registries/` (tags, layers, mechanisms, ...).
- Docs: `docs/guidelines/python_code_standard.md` and `docs/plans/codebase_health/`, as for every other domain.
