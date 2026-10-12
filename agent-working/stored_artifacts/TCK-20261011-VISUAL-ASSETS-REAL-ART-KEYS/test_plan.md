---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS
artifact_type: test_plan
tags: [architecture, testing, documentation]
---

# Test Plan: Register three optional keys, refresh snapshots

Registry loads; `test_registry.py` and `test_key_usage.py` green with exact pins; the three keys asserted optional, decorative, fallback none, no axis, detail or label; the red set is exactly the 12 `registry_mismatch` export tests until rc-0009.
