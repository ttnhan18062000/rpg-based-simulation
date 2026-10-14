---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, governance]
---

# Tech-stack seed review

Epic E, child E6, seed review (`TCK-20261009-EPIC-SESSION-LEAD-PLANNER`). It re-checks the lead's 2026-10-09
stack findings on `main` 9a9058808 (2026-10-11) and gives each one a recommendation and an owner. **Advice
only**: the fixes are tickets in the owning domain (the epic's out-of-scope list says so), and the
registry/drift-check tooling is E6's own work for agent-working.

When `registries/tech_stack.yaml` exists, it should be seeded from this list and from the inventory
below.

## Findings

| # | finding (checked 2026-10-11) | still true? | recommendation | owner | routed |
|---|---|---|---|---|---|
| 1 | `mypy` is unpinned in the `dev` group, while `mypy-baseline==0.7.4`, `ruff==0.16.10` and `import-linter==2.15` are exact. A mypy release can shift the baseline with no code change. | yes | pin `mypy==2.1.0` (exact, like the other code-health tools) | codebase | already scoped: rides the import-linter flip batch (soak ends 2026-10-19) |
| 2 | `torch` is outside the lock. | **changed** | `uv.lock` now resolves `torch 2.12.1` from PyPI (the CUDA build: it pulls `cuda-bindings` on Linux) through `sentence-transformers`. The `knowledge` extra comment still says to `pip install` the CPU wheel by hand, and `.venv-knowledge` (3.12) is built that way. So the lock and the real environment disagree. Pick one: either the lock owns it (a `[tool.uv.sources]` CPU index for torch) or the extra is documented as outside the lock. Also: `Makefile` `PYTHON_KNOWLEDGE` hard-codes the other host's path `/home/u24desktop/...`. | agent-working (knowledge-search stack) | #514 (`for:agent-working-planner`) |
| 3 | `mcp>=1.0.0` is declared twice (`search-mcp` extra and `dev`). | yes | **keep**. The `dev` entry is intentional and commented: it lets the default install reach `tests/tools/test_search_mcp.py`. Record it once in the registry, with one version policy for both declarations. | lead (registry seed) | no ticket |
| 4 | Two React apps (`frontend/`, `dashboard-frontend/`) and `website/` (Docusaurus 3), with separate `package-lock.json` files and no workspace. | yes | **no workspace now** (YAGNI). The versions match today: react `^19.2.0`, vite `^7.2.4`, tailwindcss `^4.1.18`, typescript `~5.9.3` in both apps (website: react `^19.2.7`, `@docusaurus/core ^3.10.1`). The E6 drift check reports divergence; revisit only if it fires. Merging the apps or adding a workspace is a framework change, so it needs an ADR. | lead (drift check via agent-working) | no ticket |
| 5 | `compose.yaml` `redis:7-alpine` floats; Prometheus `v2.50.0`, Grafana `10.3.3`, Loki and Promtail `3.0.0` are pinned. Redis backs `src/observability` (stream consumer, anomaly worker, readiness harness). | yes | pin an exact `7.x.y-alpine` tag, matching the observability images | rpg (consumer of redis); `compose.yaml` is lead-owned, so the lead reviews the diff | #515 (`for:rpg-planner`) |
| 6 | Root clutter. | partly | The tracked tree is clean: `uvicorn.log`, `replay_v2.json/`, `scratch/`, `tmp/` and `reviews/` are git-ignored or gone. Still **untracked**, not ignored, in the main checkout: `agent-monitoring/` and `stored_artifacts/` (27 files, old pre-`agent-working/` layout, written 2026-10-03). | owner (deleting data) | on `board.md`'s residue list |

## Inventory seed (main 9a9058808)

- **Python:** see `pyproject.toml`. The code-health tools are exact pins (`ruff`, `import-linter`, `mypy-baseline`); runtime libraries and test libraries are floors.
- **Node:** three npm projects, each with its own `package-lock.json` (row 4).
- **Containers (`compose.yaml`):** redis (floating), prometheus `v2.50.0`, grafana `10.3.3`, loki `3.0.0`, promtail `3.0.0`.
- **MCP servers:** `.mcp.json` (knowledge-search; lead-owned path).
