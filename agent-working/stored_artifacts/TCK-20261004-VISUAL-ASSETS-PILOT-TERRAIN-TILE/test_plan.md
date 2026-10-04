---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE
artifact_type: test_plan
tags: [mcp, live-map, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

Registry holds exactly `terrain.forest`; the committed catalog holds exactly one source, adoption, artifact and release candidate (and the intake copies); `audit` and `verify` clean; the stdio and adoption tests now expect the pilot asset and still fail on a second one; boundary tests unchanged.

## Proof Plan

- Level: unit and integration (real Aseprite, local only, D10).
- Proof kind: executable tests plus the store's own `audit`/`verify`.
- Oracle source: the ticket's acceptance criteria and `docs/assets/store_contract.md`.
- Expected effect: all of `tests/visual_assets` passes (1182 tests) and `audit` prints `chain ok`, `verify` prints `store ok`.
- Selected commands: `pytest tests/visual_assets` under `systemd-run --user --scope -p MemoryMax=2G`; `python -m visual_assets.store audit` and `verify`.
