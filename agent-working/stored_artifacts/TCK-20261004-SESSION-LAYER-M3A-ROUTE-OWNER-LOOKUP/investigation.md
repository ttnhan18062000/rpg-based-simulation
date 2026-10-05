---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP
phase: open
date: 2026-10-05
tags: [ai]
---

# investigation — TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP

Read the loader (`roster.py`), the manifest, the validator, and plan sections 8, 9 and 11 before writing. Findings that shaped the work:

- Path `tools/mechanism_registry/**` was owned by no domain, so AC1 could not hold without a manifest line (owner confirmed it).
