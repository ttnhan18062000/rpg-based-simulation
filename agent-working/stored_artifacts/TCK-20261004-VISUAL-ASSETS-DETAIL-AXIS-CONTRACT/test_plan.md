---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT
artifact_type: test_plan
tags: [architecture, determinism, mcp]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT

- [x] Adopt: declared, undeclared, no-axis value; same slot refused, other slot accepted; explicit default equals `None`.
- [x] Release: entries per slot sorted; default required (non-optional) and others optional; undeclared adopted value refused; ambiguous slot refused.
- [x] Manifests: unique sorted slots, entry/details consistency, bounds on entries and details.
- [x] Python and TS parsers decide 26 shared cases alike; committed fixtures and records stay byte-identical (existing round-trip, fixture and pilot tests).
- [x] Widest legal manifests and registry with detail fields read back through the real path; budget rows and parity test.

## Proof Plan
- level: unit and contract (pure Python and vitest); no Aseprite needed
- proof kind: positive and negative cases on the contracts, plus byte-identity round trips of every committed record and fixture
- oracle source: the ticket's design and `docs/assets/store_contract.md`; the shared case file is decided by both parsers
- expected effect: new slots work end to end; nothing already committed changes by one byte; bounds hold at the widest legal manifest
- selected commands: `pytest tests/visual_assets`, `npx vitest run src/visualAssets`, `npx tsc -b`, `python -m visual_assets.store verify`
