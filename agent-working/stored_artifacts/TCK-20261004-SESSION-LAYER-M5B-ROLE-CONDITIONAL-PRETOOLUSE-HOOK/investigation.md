---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Investigation: TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK

The M5B draft assumed the hook would stay inert until its script existed. Measured: a missing script exits 2 and blocks every tool call, so the wiring needs a pass-on-missing wrapper and must land with the script. The harness is fail-open on a hook crash (M0n), so the script must convert its own exceptions to exit 2 for authority classes. `state.py` has no lookup by session id; a scan over role directories is added in the guard.
