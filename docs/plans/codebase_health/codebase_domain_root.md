---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-03
tags: [architecture, planning]
---

# Codebase Domain — Where Its Tooling Lives (decision record)

## Why now

The owner asked (2026-10-03) whether codebase tooling should be better structured, or moved out of
`tools/` entirely, with long-term codebase management in mind.

## What exists (measured on `python-code-craft-gates`, b4076b46)

- `tools/` holds 329 tracked files and about 60k lines of Python: 66 flat `tools/*.py` files and
  26 subpackages, most of them agent-working (agent_codex_* ×9, agent_orchestration_* ×3,
  agent_replay_* ×2, agent-monitoring, delivery, hooks).
- **Codebase-domain material is split across five places:**
  - `tools/code_health/` (12 files: adapters, scan, ratchet, registry CLI, metrics, line_count,
    mypy_gate, sarif_feedback, staged_ratchet)
  - flat files: `codebase_health_baseline.py`, `codebase_health_snapshot.py`,
    `code_health_impact.py`, `pr_impact_report.py`, `audit_unreachable_code.py`
  - `tools/hooks/`, shared with agent-working's reindex hooks: `code_health_pre_commit.sh`,
    `uv_lock_pre_commit.sh`, `install_git_hooks.py`
  - `registries/`: `code_health_exceptions.jsonl`, `mypy_baseline.txt`
  - `agent-working/agent-monitoring/codebase_health_history.jsonl` (snapshot history; it sat in
    another domain's data root until TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE moved it to
    `codebase/reports/`)
  - plus root config (`pyproject.toml` tool sections, `.pre-commit-config.yaml`, `.jscpd.json`), docs
    (`docs/guidelines/python_code_standard.md`, `docs/plans/codebase_health/`) and tests
    (`tests/tools/test_code_health_*`, `test_codebase_health_*`, `test_mypy_gate.py`).
- **Coming in M5 to M7:** a package registry, an ast-grep rule pack with rule tests, import-linter
  contracts, and a refactor lane fed by the registry.
- **References to move:** about 60 live files name these paths (15 in agent-working tickets in
  flight, 14 in `tests/tools`, 11 inside `tools/code_health`, 10 in docs, plus the Makefile, CI,
  pyproject, the pre-commit config and one parity entry).
- **Governing rule:** `docs/guidelines/repo_tooling_layout.md` says "`tools/` is the only home for
  repo tooling" and new tools go into a `tools/` subpackage. The #289 path map keeps `registries/`
  and `tools/` in place.
- **Precedents for a domain root:** `agent-working/` (data, #289) and `visual_assets/` (a top-level
  domain root with its own Python package and MCP tools).
- **Ownership:** the codebase domain is not yet in the session-layer ownership table, so nothing
  declares which paths it owns.

## Options

**A. One package inside `tools/`:** `tools/codebase/` with `health/`, `gates/`, `hooks/`,
`reports/`. Flat files and code-health hooks move in; baselines stay in `registries/`.
- For: follows the tooling rule as written; smallest move.
- Against: the domain stays spread over `tools/`, `registries/` and `agent-working/`. Ownership
  needs several globs. M5's rule packs, contracts and package registry have no natural home.

**B. A top-level domain root `codebase/` (recommended):** everything the domain owns and changes,
in one place.
```
codebase/
  README.md            owner, map, what lives elsewhere and why
  __init__.py          importable: python3 -m codebase.health check
  health/              from tools/code_health (adapters, scan, ratchet, registry CLI, metrics, line_count)
  gates/               mypy_gate, sarif_feedback, staged_ratchet
  hooks/               prek hook scripts and install_git_hooks (from tools/hooks, code-health parts only)
  reports/             snapshot, baseline, impact, pr_impact, unreachable-code audit (from flat tools/)
  baselines/           code_health_exceptions.jsonl, mypy_baseline.txt (from registries/)
  config/              .jscpd.json (anything not required at the repository root)
  rules/, contracts/   future: ast-grep rule pack + rule tests, import-linter contracts (M5)
  packages.jsonl       future: package registry (M5)
tests/codebase/        mirror of the moved tests
```
- Stays at the root, because the tools require it there: `pyproject.toml` (ruff, complexipy,
  mypy, mypy_baseline sections), `.pre-commit-config.yaml`.
- Stays in docs: `docs/guidelines/python_code_standard.md` and `docs/plans/codebase_health/`, as
  for every other domain.
- **For:** one ownership glob (`codebase/**`) for the session-layer table and for routing. The
  M5 to M7 artifacts get a natural home. Tools and their baselines version together. The domain
  boundary is visible to agents, like `agent-working/` and `visual_assets/`.
- **Against:**
  - It amends the "tools/ is the only home" rule, an owner decision recorded in
    `repo_tooling_layout.md`. The rule's real concern was orphaned files in a second, unmaintained
    home. Mitigation: the README names the owner, and the orphan check is extended to cover
    `codebase/**`.
  - It moves two files out of `registries/`. Mitigation: the README says why; `registries/` keeps
    cross-domain registries (tags, layers, mechanisms).
  - It is a one-time move of about 25 files plus about 60 references.

**C. Do nothing structural now:** keep adding to `tools/code_health/` and decide at M5. Cheapest
now; the split grows with each milestone.

## Recommendation

B, as one ticket at the start of the next codebase batch, with no behaviour change:
- Pure moves plus reference updates, in a quiet window right after #305 merges, early in the soak,
  so the flip ticket and M5 target final paths.
- `codebase_health_history.jsonl` moved only with agent-working's agreement (given 2026-10-04 in PR #322);
  it now lives in `codebase/reports/` (TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE).
- Add the codebase domain's `owns:` entry to the session-layer table as an agent-working request,
  since agent-working owns that document.
- Acceptance:
  - CI job commands and Makefile targets keep their names, with new paths;
  - the code-health check still reports 3,617 unchanged and mypy 0 new on the PR run;
  - the orphan check covers `codebase/**`;
  - the old paths are gone, and a guard test fails if `tools/code_health` reappears.

## Owner decision (2026-10-03)

**B, top-level `codebase/`**, with the layout above. Consequence: `docs/guidelines/repo_tooling_layout.md`
is amended so that a domain root may own its tooling (`agent-working/` holds data, `visual_assets/` and
`codebase/` hold their own Python), while every tool that is not owned by such a domain root still goes into a
`tools/` subpackage, and `scripts/` stays retired.
