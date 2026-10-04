---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING
phase: open
date: 2026-10-04
tags: [ai]
---

# investigation — TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING

The transit notice lives in the old hook module, so the new hook imports it optionally (the two PRs are independent). Authority reduction needs the previous manifest, so a snapshot is kept beside the role state. `/clear` and live rename remain unprobed (class 2).
