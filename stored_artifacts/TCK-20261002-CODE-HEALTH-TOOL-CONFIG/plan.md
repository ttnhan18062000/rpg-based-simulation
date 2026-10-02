---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-TOOL-CONFIG
artifact_type: plan
tags: [setup]
---

# Plan — TCK-20261002-CODE-HEALTH-TOOL-CONFIG

1. `pyproject.toml`: pin `ruff==0.16.10` and `complexipy==8.0.1` in the `dev` group; add `[tool.ruff.lint]` (rules the standard names, preview by exact code), the mccabe and pylint thresholds, `[tool.complexipy]`, and `[tool.code_health.size]`. No `[tool.ruff.format]`.
2. `uv lock`, regenerate `requirements.txt`.
3. `tools/code_health/` package with `line_count.py`; tests in `tests/tools/test_code_health_line_count.py` covering names, boundaries, errors, CLI and configuration agreement.
4. `.jscpd.json` and Makefile targets `lint-py`, `code-health-size`, `code-health-complexity`, `code-health-dup`, all in `.PHONY`.
5. Run each tool over `src/`; record versions and results.
6. Update `python_code_standard.md` markers and `repo_tooling_layout.md`'s package list.

## Scope guards
No `src/`, `.claude/`, `CLAUDE.md`, existing test, formatter, `--fix`, adapters, ratchet or registry.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| Version and run result per tool; `uv lock --check` 0 | 1, 2, 5 |
| Real package, no `sys.path.insert` | 3 |
| Line count thresholds, nested and same-name test | 3 |
| `lint-py` check-only, in `.PHONY` | 4 |
| Ruff and complexipy thresholds match 6.1, no formatter | 1, 3 (test) |
| Orphan check live reference | 4 |
| Static tests pass unmodified | 5 |
| No `src/` diff; noqa count unchanged; tests only new | 5 |
| No `.claude/` or `CLAUDE.md` | 5 |
