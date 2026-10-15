---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE
artifact_type: test_plan
tags: [architecture, testing, mcp]
---

# Test plan: TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE

Proof Plan: level unit and integration; proof kind: equality of rc-0011 to rc-0010 plus the 18 keys, the renderer's counted draws on synthetic and real worlds, byte-identical re-render; oracle: the committed manifests, the registry and the store's own export; expected effect: the red set is green, 0 object gaps in three worlds, evidence crops equal the tool's output; selected commands: pytest tests/visual_assets (full, under MemoryMax=3G) and the files named in Test Summary.
