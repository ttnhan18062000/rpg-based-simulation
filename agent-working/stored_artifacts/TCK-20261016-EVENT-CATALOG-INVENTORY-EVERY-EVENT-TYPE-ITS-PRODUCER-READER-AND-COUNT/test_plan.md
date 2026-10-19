---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT
date: 2026-10-16
tags: []
---

# Test plan: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT

No source change, so no unit test. Checks: the static scan resolves every producer site (the 30 unresolved sites are consumers and parsers, listed in the scan output, none is a producer); the three count channels agree for every type the recorder wrote (R equals F in the 3 runs under the CRITICAL limit, L is the listener-only superset); scorer types are matched against the reachable contract types.

## Proof Plan

- level: system measurement (15 runs)
- proof kind: inventory, read-only
- oracle source: the recorder's own pre-filter counter and a kernel listener
- expected effect: none on the repo; one stored artifact
- selected commands: `python probes/static_scan.py . static.json`; `python probes/child.py <world> <seed> 5000 out.json` per run; `python probes/build_catalog.py` and `render.py`
