---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT
artifact_type: plan
tags: [architecture, determinism, mcp]
---

# Plan — TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT

1. Measure the widest legal manifests first; stop and tell the planner if a bound is exceeded (done: owner raised `MAX_MANIFEST_BYTES`, set `MAX_DETAIL_VALUES` 16, `MAX_DETAIL_KEYS` 64).
2. Contracts: `DetailAxis` + `effective_detail` on the key, `detail_value` on adoption, `detail` on release and runtime entries, `details` on the runtime manifest; absent values omitted from bytes.
3. Store: `slot_holders`, per-slot adoption refusals and `--detail`, per-slot release assembly, runtime export `details`, `verify` rules.
4. TS parser mirror and shared parity cases; bounds test, budget rows, docs, ADR D11.
