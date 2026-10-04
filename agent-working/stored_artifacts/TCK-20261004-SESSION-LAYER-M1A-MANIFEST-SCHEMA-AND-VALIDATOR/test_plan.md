---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1A-MANIFEST-SCHEMA-AND-VALIDATOR
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# Test plan

tests/tools/test_session_roster.py (24 tests): Registry files, typed loader and validator; each rule has a fixture that trips it plus a positive control; the real registry validates (this is the CI wiring: tests/tools is a CI lane).

Coverage: normal flow, each rule's failure mode with a positive control, read-only guarantees (no write, no raw dict leak), and determinism where generation is involved.
