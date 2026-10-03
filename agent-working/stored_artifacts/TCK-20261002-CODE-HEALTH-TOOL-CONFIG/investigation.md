---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-TOOL-CONFIG
artifact_type: investigation
tags: [setup]
---

# Investigation — TCK-20261002-CODE-HEALTH-TOOL-CONFIG

## Context scan
- `search_docs` (tools layout and orphan check): `docs/guidelines/repo_tooling_layout.md` (new tooling goes in a real subpackage) and `tools/gate_checks/tools_orphan_check.py`. No existing code-health package; `tools/code_health_impact.py` and `tools/codebase_health_*.py` are flat, unrelated files and stay where they are.
- `graphify query`: `check_tools_orphans()` and its tests only; nothing on lint or complexity tooling. No duplicate work.

## Findings (each tool run over `src/`, 744 files, from a scratch environment, then from the locked one)
1. **ruff 0.16.10**: works. The roadmap's own counts reproduce (9 bare `except`, 2 mutable defaults). `PLR1702` is preview-only; `preview = true` with `explicit-preview-rules = true` enables it by exact code without enabling other preview rules. `PLC0415` is stable in this version. Selecting all of `D` includes mutually conflicting rules and adds `D105`/`D107` (magic methods, `__init__`) that the standard does not ask for, so `D100` to `D104` are selected. `ANN401` is ignored because the standard makes `Any` in a signature a reviewer rule (T2).
2. **complexipy 8.0.1**: works; 3,015 functions in about 0.3 s. It reads `[tool.complexipy]` from `pyproject.toml` (confirmed by exit code: 1 at limit 15, 0 at limit 100000). It runs as a `complexipy` binary, not `python -m complexipy`. `--failed --ignore-complexity` gives a report that exits 0.
3. **jscpd 5.4.0** (Node): works through `npx`; 97 clones, 1,392 duplicated lines. npm registry is reachable from this machine.
4. **Line count** (`tools/code_health/line_count.py`): new, AST-based, `__qualname__`-style symbols.
5. **jscpd pinning decision.** The root `package.json` is the sigma/graphology graph viewer's, with a tracked `package-lock.json`; adding a dev dependency there would couple unrelated tooling and need a root `npm ci`. Instead the version is a single Makefile variable (`JSCPD_VERSION ?= 5.4.0`) used with `npx --yes jscpd@$(JSCPD_VERSION)`. This pins the version but not the dependency tree's integrity hashes; that is the accepted trade-off.
6. **Orphan checker** reads tracked files only, so `tools/code_health/` shows nothing until `git add`; `line_count.py` is `LIVE` through the Makefile and `pyproject.toml`; `__init__.py` is exempt by design.
7. **Standard drift.** `python_code_standard.md` marked these tools "planned"; its ownership row names that as a staleness signal once they are configured. Updated to "configured" (not gated) with the run commands.
8. **No `src/` edit is needed or made**; the `# noqa` / `# type: ignore` count under `src/` stays at 23.
