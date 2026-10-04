---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT
artifact_type: plan
tags: [architecture, determinism, mcp]
---

# Plan — TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT

1. `pickDetail.ts` (FNV-1a over `key|x|y|seed`, mod declared values, fixed seed) with golden vectors computed independently in Python.
2. `resolveVisual` takes an optional cell; a key in `details` resolves picked -> default -> role fallback and records `picked`, `detail`, `detailFallback`; keys without an axis keep the old path.
3. `View.resolve(key, cell?)`, `drawTerrainCell`/`drawPilotScene` pass the cell.
4. Tests, two mutants, 64 x 64 spread, contract paragraph in `store_contract.md`.
