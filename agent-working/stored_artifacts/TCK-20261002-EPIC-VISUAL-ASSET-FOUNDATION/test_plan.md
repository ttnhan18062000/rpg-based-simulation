---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION
artifact_type: test_plan
tags: [mcp, architecture, documentation]
---

# Test plan (roll-up) — TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION

## Proof Plan

| Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|
| per child | each child's own proof plan (unit, integration with real Aseprite, stdio, architecture, mutation) | the child's acceptance criteria | every child's criteria ticked with evidence | see `agent-working/stored_artifacts/TCK-20261002-VISUAL-ASSETS-*/test_plan.md` |
| architecture | the boundary test: no `src` coupling, store layering rows, only `store/build` imports the sandbox, the drawing code cannot import any writer, the server imports only `intake` and `readmodel` | `tests/visual_assets/test_boundaries.py` and its planted violations | boundary test green | `pytest tests/visual_assets/test_boundaries.py` |
| whole store | the committed catalog verifies clean in CI and holds no real asset | `tests/visual_assets/test_catalog_integrity.py` | no blocking finding | `pytest tests/visual_assets/test_catalog_integrity.py` |
| docs | every documented command and MCP tool exists and vice versa | `tests/visual_assets/store/unit/test_docs_commands.py` | no drift | same |
| CI-like | everything that needs no Aseprite | `ASEPRITE_MCP_BINARY=/nonexistent pytest tests/visual_assets` | green (870 passed, 201 skipped at close) | same |
| local | the real-Aseprite tests | pinned Aseprite 1.3.18.6 | green (1071 passed at close) | `pytest tests/visual_assets` |
