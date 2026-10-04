---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT
phase: open
date: 2026-10-04
tags: [ai, hooks, process-improvement]
---

# plan — TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT

1. `tools/handover_transit.py` (export/import/status/discard; pure functions with injected paths for tests).
2. Hook: `build_transit_notice` + `main` accepts startup/resume/clear (handover listing stays clear-only). Matcher is already `*` in settings.json, so no governing-file edit.
3. Guide section + delivery_process step 2a.
4. Tests in tests/tools/test_handover_transit.py.
5. Close: registry regen, closure recorder, done_checker_static, final rolling export staged with the PR.
